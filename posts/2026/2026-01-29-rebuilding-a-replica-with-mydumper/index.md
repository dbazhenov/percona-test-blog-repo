---
title: "Rebuilding a Replica with MyDumper"
id: "2026-01-29-rebuilding-a-replica-with-mydumper"
date: "2026-01-29T14:40:22Z"
draft: false
origin: percona
description: "When a replica fails due to corruption or drift, the standard solution is to rebuild it from a fresh copy of the master when pt-table-sync is not an option. Traditionally, when we need to build a new replica, we use a physical backup for speed, but there are some cases where you…"
authors:
  - david-ducos
categories:
  - "MySQL"
tags:
  - "mydumper"
  - "MySQL"
  - "mysql-and-variants"
images:
  - Percona_Texture_186.jpg
slug: rebuilding-a-replica-with-mydumper
---

![Rebuilding a Replica with MyDumper](Percona_Texture_186.jpg)

When a replica fails due to corruption or drift, the standard solution is to rebuild it from a fresh copy of the master when pt-table-sync is not an option. Traditionally, when we need to build a new replica, we use a physical backup for speed, but there are some cases where you still need logical backups. For instance, when you migrate to a specific vendor (i.e.: MariaDB to MySQL) or storage engines (in the past MyISAM to InnoDB and nowadays from InnoDB to RocksDB), upgrade to a new database version or move to a cloud based solution. This is where a logical backup shines, offering portability and simplicity, but only if it can be performed quickly. MyDumper emerges as the essential, modern solution, delivering the best of both worlds: the cross-platform, cross-version flexibility of a logical dump combined with the parallel, multi-threaded speed previously reserved for physical methods, making it the clear choice for rapidly rebuilding a consistent replica.

# Take the backup

The first step is to take the backup. We have multiple arguments which we can use with mydumper, for this example we are going to use:

```
mydumper -v 4 -o data --clear 
--regex '^(?!(mysql.|sys.))' 
--source-data
```

The first 3 are related to logging and backup dir, the second line is for ignoring mysql and sys schemas and finally –source-data will instruct mydumper to save in the metadata file, all the info required for the replication configuration after the restore under the section [source].

This is an example of the output:

```
[source]
# Channel_Name = '' # It can be used to setup replication FOR CHANNEL
# SOURCE_LOG_FILE = "binlog.000020"
# SOURCE_LOG_POS = 6803936
#SOURCE_HOST = "172.17.0.3"
#SOURCE_PORT =
#SOURCE_USER = ""
#SOURCE_PASSWORD = ""
#SOURCE_SSL = {0|1}
executed_gtid_set = "941fdce6-47c4-11f0-87b2-0242ac110006:1-52"
SOURCE_LOG_FILE = "binlog.000020"
SOURCE_LOG_POS = 6803936
#SOURCE_AUTO_POSITION = {0|1}
myloader_exec_reset_replica = 0
myloader_exec_change_source = 0
myloader_exec_start_replica = 0
```

As we can see, this options are enabled:

```
executed_gtid_set = "941fdce6-47c4-11f0-87b2-0242ac110006:1-52"
SOURCE_LOG_FILE = "binlog.000020"
SOURCE_LOG_POS = 6803936
```

However, the execution of the commands are disabled:

```
myloader_exec_reset_replica = 0
myloader_exec_change_source = 0
myloader_exec_start_replica = 0
We can enable them, if we set --source-data=7, then the metadata will change to:
myloader_exec_reset_replica = 1
myloader_exec_change_source = 1
myloader_exec_start_replica = 1
```

Which is needed to automatically configure the replication.

# Configure replication

By default, the SOURCE_LOG_FILE and SOURCE_LOG_POS will be used, but you can set the GTID position if you configure SOURCE_AUTO_POSITION = 1.

As you might know, to set up replication we need to execute CHANGE SOURCE. However, depending on your use case, you might need to RESET REPLICA and after executing the CHANGE SOURCE you usually execute START REPLICA. This can be done by myloader automatically if you set it up in the metadata file using:

```
myloader_exec_reset_replica = 1
myloader_exec_change_source = 1
myloader_exec_start_replica = 1
```

Or you can use –source-data=7 as a parameter in myloader. Yes! myloader also accepts –source-data.

Depending your use case, you might need to configure in the metadata file, this other options:

```
#SOURCE_HOST = "172.17.0.3"
#SOURCE_PORT =
#SOURCE_USER = ""
#SOURCE_PASSWORD = ""
#SOURCE_SSL = {0|1}
executed_gtid_set = "941fdce6-47c4-11f0-87b2-0242ac110006:1-52"
SOURCE_LOG_FILE = "binlog.000020"
SOURCE_LOG_POS = 6803936
#SOURCE_AUTO_POSITION = {0|1}
```

As there are multiple use cases:

If you want want to rebuild the replica from scratch then you will need to configure like this:

```
[source]
SOURCE_HOST = "172.17.0.3"
SOURCE_PORT = 3306
SOURCE_USER = "replica"
SOURCE_PASSWORD = "r3pl1c4"
executed_gtid_set = "941fdce6-47c4-11f0-87b2-0242ac110006:1-52"
SOURCE_LOG_FILE = "binlog.000020"
SOURCE_LOG_POS = 6803936
myloader_exec_reset_replica = 1
myloader_exec_change_source = 1
myloader_exec_start_replica = 1
```

You already have a replication up and running and you want to rebuild it without changing the host or credentials, then you can configure just in this way:

```
[source]
executed_gtid_set = "941fdce6-47c4-11f0-87b2-0242ac110006:1-52"
SOURCE_LOG_FILE = "binlog.000020"
SOURCE_LOG_POS = 6803936
myloader_exec_reset_replica = 0
myloader_exec_change_source = 1
myloader_exec_start_replica = 1
```

SSL is another option that is possible to set up in –source-data on myloader, instead of using SOURCE_SSL on the metadata file. The full list of options are: exec_start_slave (1), exec_change_master (2), exec_reset_slave (4), SSL (8), auto_position (16) and exec_start_replica_until (32). Depending on the configuration that you want to set up and the statements that you want to execute, you will need to sum the values and pass it to –source-data.

# Restore

After configure the metadata file, you can execute the myloader, which will look like:

```
myloader -d data -v 4 
-o --max-threads-for-schema-creation=1 
-h replica_host
```

In the log, you will find that myloader has send the commands:

```
2025-12-18 16:57:09 [INFO] - Schema create checksum confirmed for sakila
2025-12-18 16:57:09 [INFO] - Sending reset replica
2025-12-18 16:57:09 [INFO] - Sending change replication source
2025-12-18 16:57:09 [INFO] - Sending start replica
2025-12-18 16:57:09 [INFO] - Restore completed
```

mydumper is sending the command but is not checking the output which means that if the replication failed to configure or it was not able to start, you will need to manually check it and fix it. However, it will detect if the command failed, for example if SUORCE_USER is used instead of SOURCE_USER:

```
2025-12-18 17:02:56 [WARNING] - Sending replication command: CHANGE REPLICATION SOURCE TO SOURCE_HOST = "172.17.0.4", SUORCE_USER = "root", SOURCE_PASSWORD = "", SOURCE_LOG_FILE = "binlog.000020", SOURCE_LOG_POS = 1362220 FOR CHANNEL ''; - ERROR 1064: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'SUORCE_USER = "root", SOURCE_PASSWORD = "", SOURCE_LOG_FILE = "binlog.000020", SO' at line 1
```

# Partial rebuild on a stopped replica

There is an interesting use case where we can use START REPLICA UNTIL to fix drift on some tables where pt-table-sync or rebuilding the whole replica are not possible.

Let’s say we have a source and a replica, and we found that data has drifted on the replica and the replication process has stopped with an error like this:

```
LAST_ERROR_MESSAGE: Worker 1 failed executing transaction 'ANONYMOUS' at source log binlog.000020, end_log_pos 1369103; Could not execute Update_rows event on table test.test_table; Can't find record in 'test_table', Error_code: 1032; handler error HA_ERR_KEY_NOT_FOUND; the event's source log binlog.000020, end_log_pos 1369103
```

We checked the binary log and it is failing due updates over a set of rows:

```
# at 1368995
#251218 19:34:59 server id 1 end_log_pos 1369103 CRC32 0x60a481d6 Update_rows: table id 344 flags: STMT_END_F
### UPDATE `test`.`test_table`
### WHERE
### @1=12 /* INT meta=0 nullable=0 is_null=0 */
### @2=7062 /* INT meta=0 nullable=1 is_null=0 */
### SET
### @1=12 /* INT meta=0 nullable=0 is_null=0 */
### @2=7063 /* INT meta=0 nullable=1 is_null=0 */
### UPDATE `test`.`test_table`
### WHERE
### @1=15 /* INT meta=0 nullable=0 is_null=0 */
### @2=7521 /* INT meta=0 nullable=1 is_null=0 */
### SET
### @1=15 /* INT meta=0 nullable=0 is_null=0 */
### @2=7522 /* INT meta=0 nullable=1 is_null=0 */
### UPDATE `test`.`test_table`
### WHERE
### @1=17 /* INT meta=0 nullable=0 is_null=0 */
### @2=8706 /* INT meta=0 nullable=1 is_null=0 */
### SET
### @1=17 /* INT meta=0 nullable=0 is_null=0 */
### @2=8707 /* INT meta=0 nullable=1 is_null=0 */
### UPDATE `test`.`test_table`
### WHERE
### @1=18 /* INT meta=0 nullable=0 is_null=0 */
### @2=8108 /* INT meta=0 nullable=1 is_null=0 */
### SET
### @1=18 /* INT meta=0 nullable=0 is_null=0 */
### @2=8109 /* INT meta=0 nullable=1 is_null=0 */
# at 1369103
```

We check the database and it is true, the data has drifted:

Source:

```
mysql> select count(*) from test.test_table;
+----------+
| count(*) |
+----------+
| 15 |
+----------+
1 row in set (0.00 sec)
```

Replica:

```
mysql> select count(*) from test.test_table;
+----------+
| count(*) |
+----------+
| 14 |
+----------+
1 row in set (0.00 sec)
```

With MyDumper we can rebuild the table following this procedure:

We need to ignore the table to allow the replica to catchup

```
mysql-replica> STOP REPLICA;
Query OK, 0 rows affected (0.00 sec)

mysql-replica> CHANGE REPLICATION FILTER REPLICATE_IGNORE_TABLE= (test.test_table);
Query OK, 0 rows affected (0.00 sec)

mysql-replica> START REPLICA;
Query OK, 0 rows affected (0.00 sec)
```

Once that the replica is up to date we need to stop the replica:

```
mysql-replica> STOP REPLICA;
Query OK, 0 rows affected (0.00 sec)
```

and take the backup on the Source server:

```
mydumper -v 4 -o data --clear 
-T test.test_table 
--source-data
```

We are using -T to take the backup of the problematic table and –source-data will enable the replication variables that we need on the metadata file.

Then, we restore the table with the correct value on –source-data

```
myloader -d data -v 4 
-o --max-threads-for-schema-creation=1 
-h replica_host 
--source-data=32
```

The 32 is to execute the START REPLICA UNTIL.

Finally, we remove the ignore table option and start the replica again:

```
mysql-replica> CHANGE REPLICATION FILTER REPLICATE_IGNORE_TABLE= ();
Query OK, 0 rows affected (0.00 sec)

mysql-replica> START REPLICA;
Query OK, 0 rows affected (0.00 sec)
```

The START REPLICA UNTIL executed at the beginning of backup by myloader will force the replica to stop at the point where we took the backup of the table, allowing us to continue the replication in a consistent scenario.

# Conclusions

The shift from legacy dumping methods to MyDumper represents more than just a performance boost; it represents a modernized approach to data integrity and mobility. By decoupling the backup process from the constraints of single-threaded execution, DBAs can now handle massive datasets with the same agility they once reserved for small test environments.

Incorporating MyDumper into your standard operational playbook ensures you are prepared for the unpredictable—whether it’s an emergency replica rebuild or a planned architectural migration. In an era where data volumes continue to scale exponentially, having a tool that balances logical flexibility with parallelized speed, MyDumper becomes a necessity. Keep it in your toolkit, and the next time you face a “logical-only” recovery scenario, you’ll be doing so with a significant competitive advantage.
