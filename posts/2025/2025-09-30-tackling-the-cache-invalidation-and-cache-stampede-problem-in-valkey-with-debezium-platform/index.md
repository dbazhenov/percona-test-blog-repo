---
title: "Tackling the Cache Invalidation and Cache Stampede Problem in Valkey with Debezium Platform"
id: "2025-09-30-tackling-the-cache-invalidation-and-cache-stampede-problem-in-valkey-with-debezium-platform"
date: "2025-09-30T13:17:13Z"
draft: false
origin: percona
description: "There are two hard problems in computer science: cache invalidation, naming things, and off-by-1 errors. This classic joke, often attributed to Phil Karlton, highlights a very real and persistent challenge for software developers. We’re constantly striving to build faster, more…"
authors:
  - hieu-nguyen
categories:
  - "Valkey"
tags:
  - "cdc"
  - "MySQL"
  - "Valkey"
images:
  - Percona_Texture_233.jpg
slug: tackling-the-cache-invalidation-and-cache-stampede-problem-in-valkey-with-debezium-platform
---

![Tackling the Cache Invalidation and Cache Stampede Problem in Valkey with Debezium Platform](Percona_Texture_233.jpg)

There are two hard problems in computer science: cache invalidation, naming things, and off-by-1 errors.

This classic joke, often attributed to Phil Karlton, highlights a very real and persistent challenge for software developers. We’re constantly striving to build faster, more responsive systems, and caching is a fundamental strategy for achieving that.

But while caching offers a significant performance boost, it introduces a complex new problem: how do you ensure the cached data is always fresh and accurate? This challenge is known as cache invalidation, and if it’s not handled correctly, it can lead to stale data being served to users or, in a worst-case scenario, trigger a catastrophic chain reaction called a cache stampede.

In this blog post, we will attempt to tackle these problems in Valkey using the Debezium platform.

## What exactly is Cache Invalidation and Cache Stampede?

Before we explore these problems further, we must understand what “cache invalidation” and “cache stampede” are.

One common use case for [Valkey](https://www.percona.com/valkey) is Database Query Cache, where you store the results of database queries in Valkey to improve the processing time for a request and reduce the load on your database systems.

But as Valkey is a separate system from the database, how will it know when the query result(s) it cached are updated and begin serving the new data? This is what Cache Invalidation is: when changes are being made to the dataset, for example, an UPDATE statement is executed against the database, we need a way to invalidate the data stored in Valkey to ensure that the updated data is reflected. If the cache is not invalidated, there is a risk of displaying outdated information to users, which can cause confusion or even privacy issues.

Cache Invalidation is often dealt with by setting an expiration date for the cached data. When the data is not present in the cache (a cache miss), either because the entry has expired and been removed from Valkey or it did not exist in Valkey in the first place, applications will fetch it from the database layer, and store it in the cache for future use.

But if there are too many cache misses at the same time, either because multiple cache entries expire at the same time or because too many sessions request the same expired entries, it will cause a huge spike in database load. In the worst-case scenario, this will lead to performance degradation or crashes because each connection will attempt to update the missing cache entry from the database. This problem is called Cache Stampede.

## Tackling the problems with Change Data Capture

Change Data Capture, or CDC, is the process/design pattern for capturing changes to data, such as executing INSERT, UPDATE, and DELETE statements in a MySQL database. These changes can then be applied to other data stores like data warehouses and data lakes, enabling real-time data processing and delivering time-sensitive insights.

CDC can also be used for updating caches, which is the use case discussed in this blog post.

## Setting up a CDC pipeline from MySQL to Valkey using the Debezium Platform

From the Debezium documentation:

> Debezium is a set of distributed services to capture changes in your databases so that your applications can see those changes and respond to them. Debezium records all row-level changes within each database table in a change event stream, and applications simply read these streams to see the change events in the same order in which they occurred.

Debezium is a popular open-source solution for CDC. It supports capturing data from widely used database systems, such as MySQL, PostgreSQL, MongoDB, etc. Debezium provides the debezium-api module, allowing us to easily configure a Debezium connector in a Java project.

For the demo, we will set up a small Java program to stream changes from MySQL to Valkey as a JSON object.

### Dependencies

To start with the demo project, we will need to install a few things on the system

- OpenJDK: for this blog post, I’m using JDK version 17.

- Apache Maven: for managing the Java project dependencies.

- Docker: for deploying the MySQL and Valkey instances.

For this demo, we will need dependencies for Debezium, MySQL, and Valkey using Maven. This entails adding the following to your application’s POM, where ${version.debezium} is the version of Debezium Platform you’re using, or a Maven property whose value contains the Debezium version string, which for me is 3.3.0.Alpha2 – the latest available at the time of writing.

```
<dependency>
    <groupId>io.debezium</groupId>
    <artifactId>debezium-api</artifactId>
    <version>${version.debezium}</version>
</dependency>
<dependency>
    <groupId>io.debezium</groupId>
    <artifactId>debezium-embedded</artifactId>
    <version>${version.debezium}</version>
</dependency>
<dependency>
    <groupId>io.debezium</groupId>
    <artifactId>debezium-connector-mysql</artifactId>
    <version>${version.debezium}</version>
</dependency>
<dependency>
    <groupId>io.valkey</groupId>
    <artifactId>valkey-java</artifactId>
    <version>LATEST</version>
</dependency>
```

## In the code

### Defining the connection to MySQL

We will begin by defining the configuration for the MySQL connector, which connects to an instance running on localhost:3306 with the user ‘mysqluser’.

```
Properties props = new Properties(); 
props.setProperty("name", "engine");
props.setProperty("connector.class", "io.debezium.connector.mysql.MySqlConnector"); 
props.setProperty("offset.flush.interval.ms", "60000"); 
// define database connection
props.setProperty("database.hostname", "localhost"); 
props.setProperty("database.port", "3306"); 
props.setProperty("database.user", "mysqluser"); 
props.setProperty("database.password", "<your actual password>"); 
props.setProperty("database.server.id", "85744"); 

// define connector metadata storage
props.setProperty("topic.prefix", "my-app-connector"); 
props.setProperty("schema.history.internal", "io.debezium.storage.file.history.FileSchemaHistory"); 
props.setProperty("schema.history.internal.file.filename", "/tmp/schemahistory.dat"); 
props.setProperty("offset.storage", "org.apache.kafka.connect.storage.FileOffsetBackingStore"); 
props.setProperty("offset.storage.file.filename", "/tmp/offsets.dat"); 

// disable schema portion in the ChangeEvent for smaller message 
props.setProperty("value.converter.schemas.enable", "false"); 
props.setProperty("key.converter.schemas.enable", "false");
```

When the connector runs, it reads information from the source and periodically records “offsets” that define how much of that information it has processed. If the process is restarted, it can continue from where it left off, preventing duplicate messages, which could affect data integrity if not handled carefully.

Debezium MySQL connector reads the server’s binary logs, which include all data changes and schema changes made to the databases. Since all changes to data are structured in terms of the owning table’s schema at the time the change was recorded, the connector needs to track all of the schema changes so that it can properly decode the change events. The connector records the schema information so that, should the connector be restarted and resume reading from the last recorded offset, it knows exactly what the database schemas looked like at that offset.

In this demo, we will store both the offset information and the database schema history as local files on the system, at /tmp/offsets.dat for the offset, and /tmp/schemahistory.dat for the schema history.

Lastly, for a CDC engine to automatically and accurately sync data between different database systems, it needs to know a few things about the metadata/schema of the data it is syncing, i.e, what is the datatype of a column/field, how big should a column be, etc. As such, there needs to be a schema for the engine to identify the structure of the database, or has it been changed recently, in order to replicate the data as accurately as possible. But in cases like streaming changes to a non-RDBMS data store, we do not need those schemas, so they can be disabled/removed from the event for a smaller message and faster processing speed.

### Printing the change event to the console

After specifying the configuration, we can create an instance of DebeziumEngine. This object will poll the MySQL server every 10 milliseconds and print to the console each ChangeEvent captured.

```
DebeziumEngine<ChangeEvent<String, String>> engine = DebeziumEngine.create(Json.class, Json.class) 
   .using(props) 
   .notifying(r -> {
       System.out.println(r.value());
   })
   .build(); 
ScheduledExecutorService executor = Executors.newSingleThreadScheduledExecutor(); 
executor.scheduleAtFixedRate(engine, 0, 10, TimeUnit.MILLISECONDS);
```

The output to the console will resemble this

```
Sep 15, 2025 11:33:07 AM com.github.shyiko.mysql.binlog.BinaryLogClient requestBinaryLogStreamMysql
INFO: Requesting streaming from position filename: binlog.000002, position: 3258
Sep 15, 2025 11:33:07 AM com.github.shyiko.mysql.binlog.BinaryLogClient connect
INFO: Connected to localhost:3306 at binlog.000002/3258 (sid:85744, cid:26)
{"before":null,"after":{"id":1,"value":"hello world"},"source":{"version":"3.3.0.Alpha2","connector":"mysql","name":"my-app-connector","ts_ms":1757910721000,"snapshot":"false","db":"test","sequence":null,"ts_us":1757910721000000,"ts_ns":1757910721000000000,"table":"t","server_id":1,"gtid":null,"file":"binlog.000002","pos":3467,"row":0,"thread":16,"query":null},"transaction":null,"op":"c","ts_ms":1757910787191,"ts_us":1757910787191237,"ts_ns":1757910787191237000}
```

### Writing the change event to Valkey using JSON.SET

While JSON has become a built-in datatype for Redis, it is not the case for Valkey (yet). As such, the client library will not provide us with JSON commands. But we can do a quick implementation of it by using the ProtocolCommand interface

```
public enum Command implements ProtocolCommand { 
   JSON_SET("JSON.SET"); 
   private final byte[] raw; 
   Command(String str) { 
       raw = str.getBytes();
   }
   @Override 
   public byte[] getRaw() { 
       return raw; 
   }
}
```

Then we can write the change event to Valkey as a JSON object:

```
String valkeyHostname = "localhost";
int valkeyPort = 6379;
JedisPool jedisPool = new JedisPool(valkeyHostname, valkeyPort);
DebeziumEngine<ChangeEvent<String, String>> engine = DebeziumEngine.create(Json.class, Json.class) 
   .using(props) 
   .notifying(r -> {
       jedisPool.getResource().sendCommand(Command.JSON_SET, r.key(), ".", r.value());
   })
   .build(); 
ScheduledExecutorService executor = Executors.newSingleThreadScheduledExecutor(); 
executor.scheduleAtFixedRate(engine, 0, 10, TimeUnit.MILLISECONDS);
```

### Modifying the change event before writing to Valkey

Looking at the output of the JSON.SET command, we can see that while the change event does appear on Valkey, the data is not very helpful: the key does not tell us what table/key pattern it belongs to, and the value contains unnecessary information (e.g., the application using the key most likely won’t need to know the binlog detail).

```
127.0.0.1:6379> keys *
1) "{"id":1}"
127.0.0.1:6379> JSON.GET "{"id":1}"
"{"before":null,"after":{"id":1,"value":"hello world"},"source":{"version":"3.3.0.Alpha2","connector":"mysql","name":"my-app-connector","ts_ms":1757911355000,"snapshot":"false","db":"test","sequence":null,"ts_us":1757911355000000,"ts_ns":1757911355000000000,"table":"t","server_id":1,"gtid":null,"file":"binlog.000002","pos":5588,"row":0,"thread":16,"query":null},"transaction":null,"op":"c","ts_ms":1757911355791,"ts_us":1757911355791396,"ts_ns":1757911355791396000}"
```

If we need more advanced processing of the ChangeEvent record before writing it to the cache (for example, transforming the record key to formats like <table-name>:<primary-key-value>, or removing the change event metadata from the record), we can use the io.debezium.engine.DebeziumEngine.ChangeConsumer<R> to do it.

In the following example, we will transform the record so that:

- The ChangeEvent key will be in the format <table-name>:<id>

- Remove all metadata from the ChangeEvent value.

- Delete the key from cache if the event we are processing is a DELETE statement (optype: “d”).

```
public class ValkeyChangeConsumer implements DebeziumEngine.ChangeConsumer<ChangeEvent<String, String>> {
   @Override
   public void handleBatch( 
           List<ChangeEvent<String, String>> list,
           DebeziumEngine.RecordCommitter<ChangeEvent<String, String>> recordCommitter 
   ) throws InterruptedException { 
       for (ChangeEvent<String, String> event : list) { 
           try { 
               JSONObject recV = new JSONObject(event.value()); 
               String opType = recV.getString("op"); 
               String key; 
               if (opType.equalsIgnoreCase("d")) { 
                   key = String.valueOf(recV.getJSONObject("before").get("id")); 
               } else { 
                   key = String.valueOf(recV.getJSONObject("after").get("id"));
               } 
               String tableName = recV.getJSONObject("source").getString("table");
               String valkeyK = String.format("%s:%s", tableName, key);
               if (opType.equalsIgnoreCase("d")) {
                   jedisPool.getResource().del(valkeyK); 
               } else {
                   String valkeyV = recV.getJSONObject("after").toString(); 
                   jedisPool.getResource().sendCommand(Command.JSON_SET, valkeyK, ".", valkeyV); 
               }
               recordCommitter.markProcessed(event);
           } catch (Exception e) {
               e.printStackTrace(); 
           }
       }
       recordCommitter.markBatchFinished(); 
   }
}
```

We can then use ValkeyChangeConsumer by passing an instance of it to the notifying API

```
DebeziumEngine<ChangeEvent<String, String>> engine = DebeziumEngine.create(Json.class, Json.class) 
       .using(props)
       .notifying(new ValkeyChangeConsumer()) 
       .build();
```

The change event is presented much better on Valkey now

```
127.0.0.1:6379> keys *
1) "t:1"

127.0.0.1:6379> JSON.GET t:1
"{"id":1,"value":"hello world"}"
```

## Putting it all together

The source code for the Java program is available on the Percona Lab GitHub account: [https://github.com/Percona-Lab/valkey-cdc-debezium](https://github.com/Percona-Lab/valkey-cdc-debezium)

First, we will deploy the MySQL and Valkey instance.

– For MySQL, we will create the user mysqluser

– For Valkey, we will use the valkey-bundle Docker image, which includes valkey-json, valkey-search, and valkey-ldap modules.

```
docker run --name mysql -e MYSQL_ROOT_PASSWORD=<your actual password> -p 3306:3306 -d percona/percona-server:8.4
docker exec -ti mysql mysql -uroot -pmy-secret-pw -e "CREATE USER 'mysqluser'@'%' IDENTIFIED BY '<your actual password>';"
docker exec -ti mysql mysql -uroot -pmy-secret-pw -e "GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'mysqluser'@'%';"
docker run --name valkey -p 6379:6379 -d valkey/valkey-bundle:9.0-rc1-alpine
```

Download the Java program source code and compile it. Before compiling, please remember to update the database password config key.

```
wget https://github.com/Percona-Lab/valkey-cdc-debezium/archive/refs/heads/main.zip
unzip main.zip
cd valkey-cdc-debezium-main
mvn clean package
```

Running the program

```
java -jar target/dbewithvalkey-1.0-SNAPSHOT.jar
```

## Summary

This integration of Change Data Capture (CDC) with Valkey offers significant benefits for managing cache invalidation and stampede problems. By leveraging Debezium Engine to stream database changes in real-time to Valkey, applications can ensure their cached data is always up-to-date, reducing the risk of serving stale information and the risk of Cache Stampede occurring.

### Further reading

- Debezium Engine documentation: [https://debezium.io/documentation/reference/stable/development/engine.html](https://debezium.io/documentation/reference/stable/development/engine.html)
