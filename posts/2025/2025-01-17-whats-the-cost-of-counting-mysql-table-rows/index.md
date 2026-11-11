---
title: "What’s the Cost of Counting MySQL Table Rows?"
id: "2025-01-17-whats-the-cost-of-counting-mysql-table-rows"
date: "2025-01-17T15:19:26Z"
draft: false
origin: percona
description: "What index will be used when you count all rows in a table? Well, the MySQL documentation provides a straightforward answer to this, quoting: InnoDB processes SELECT COUNT(*) statements by traversing the smallest available secondary index unless an index or optimizer hint direct…"
authors:
  - przemek-malkowski
categories:
  - "MySQL"
tags:
  - "MySQL"
  - "mysql-and-variants"
images:
  - Percona_Texture_219.jpg
slug: whats-the-cost-of-counting-mysql-table-rows
---

![What’s the Cost of Counting MySQL Table Rows?](Percona_Texture_219.jpg)

What index will be used when you count all rows in a table? Well, the [MySQL documentation](https://dev.mysql.com/doc/refman/8.4/en/aggregate-functions.html#function_count) provides a straightforward answer to this, quoting:

> InnoDB processes `SELECT COUNT(*)` statements by traversing the smallest available secondary index unless an index or optimizer hint directs the optimizer to use a different index. If a secondary index is not present, InnoDB processes `SELECT COUNT(*)` statements by scanning the clustered index.

And how do we measure the cost of such a counting query? Is it like any other query type?

With a simple sysbench table example, first let’s check the query plan:

```
mysql > explain select count(*) from sbtest1;
+----+-------------+---------+------------+-------+---------------+------+---------+------+--------+----------+-------------+
| id | select_type | table   | partitions | type  | possible_keys | key  | key_len | ref  | rows   | filtered | Extra       |
+----+-------------+---------+------------+-------+---------------+------+---------+------+--------+----------+-------------+
|  1 | SIMPLE      | sbtest1 | NULL       | index | NULL          | k_1  | 4       | NULL | 986400 |   100.00 | Using index |
+----+-------------+---------+------------+-------+---------------+------+---------+------+--------+----------+-------------+
1 row in set, 1 warning (0.00 sec)
```

As expected, the query optimizer chose the secondary index and intends to do a scan on it. Running the query will increment handlers accordingly and report the same in the slow log:

```
mysql > flush status;
Query OK, 0 rows affected (0.00 

mysql > select count(*) from sbtest1;
+----------+
| count(*) |
+----------+
|  1000000 |
+----------+
1 row in set (0.17 sec)

mysql > show status like 'Handler_read%';
+-----------------------+---------+
| Variable_name         | Value   |
+-----------------------+---------+
| Handler_read_first    | 1       |
| Handler_read_key      | 1       |
| Handler_read_last     | 0       |
| Handler_read_next     | 1000000 |
| Handler_read_prev     | 0       |
| Handler_read_rnd      | 0       |
| Handler_read_rnd_next | 0       |
+-----------------------+---------+
7 rows in set (0.01 sec)
```

The first surprise is that the slow log does not report any `rows_examined` after the above execution:

```
# Time: 2025-01-12T15:35:28.548037Z
# User@Host: msandbox[msandbox] @ localhost []  Id:     9
# Schema: db1  Last_errno: 0  Killed: 0
# Query_time: 0.173279  Lock_time: 0.000006  Rows_sent: 1  Rows_examined: 0  Rows_affected: 0  Bytes_sent: 62
use db1;
SET timestamp=1736696128;
select count(*) from sbtest1;
```

What if there is no secondary key available? The second example table has only the primary key defined:

```
mysql > desc sbtest2;
+-------+-----------+------+-----+---------+----------------+
| Field | Type      | Null | Key | Default | Extra          |
+-------+-----------+------+-----+---------+----------------+
| id    | int       | NO   | PRI | NULL    | auto_increment |
| k     | int       | NO   |     | 0       |                |
| c     | char(120) | NO   |     |         |                |
| pad   | char(60)  | NO   |     |         |                |
+-------+-----------+------+-----+---------+----------------+
4 rows in set (0.01 sec)

mysql > explain select count(*) from sbtest2;
+----+-------------+---------+------------+-------+---------------+---------+---------+------+--------+----------+-------------+
| id | select_type | table   | partitions | type  | possible_keys | key     | key_len | ref  | rows   | filtered | Extra       |
+----+-------------+---------+------------+-------+---------------+---------+---------+------+--------+----------+-------------+
|  1 | SIMPLE      | sbtest2 | NULL       | index | NULL          | PRIMARY | 4       | NULL | 986400 |   100.00 | Using index |
+----+-------------+---------+------------+-------+---------------+---------+---------+------+--------+----------+-------------+
1 row in set, 1 warning (0.00 sec)
```

Here comes the second surprise: handlers do not change!

```
mysql > flush status;
Query OK, 0 rows affected (0.00 sec)

mysql > select count(*) from sbtest2;
+----------+
| count(*) |
+----------+
|  1000000 |
+----------+
1 row in set (0.04 sec)

mysql > show status like 'Handler_read%';
+-----------------------+-------+
| Variable_name         | Value |
+-----------------------+-------+
| Handler_read_first    | 0     |
| Handler_read_key      | 0     |
| Handler_read_last     | 0     |
| Handler_read_next     | 0     |
| Handler_read_prev     | 0     |
| Handler_read_rnd      | 0     |
| Handler_read_rnd_next | 0     |
+-----------------------+-------+
7 rows in set (0.00 sec)
```

Will the same query cost differ in yet another table, this time without any index defined?

```
mysql > desc sbtest3;
+-------+-----------+------+-----+---------+-------+
| Field | Type      | Null | Key | Default | Extra |
+-------+-----------+------+-----+---------+-------+
| id    | int       | NO   |     | 0       |       |
| k     | int       | NO   |     | 0       |       |
| c     | char(120) | NO   |     |         |       |
| pad   | char(60)  | NO   |     |         |       |
+-------+-----------+------+-----+---------+-------+
4 rows in set (0.00 sec)

mysql > explain select count(*) from sbtest3;
+----+-------------+---------+------------+------+---------------+------+---------+------+--------+----------+-------+
| id | select_type | table   | partitions | type | possible_keys | key  | key_len | ref  | rows   | filtered | Extra |
+----+-------------+---------+------------+------+---------------+------+---------+------+--------+----------+-------+
|  1 | SIMPLE      | sbtest3 | NULL       | ALL  | NULL          | NULL | NULL    | NULL | 985734 |   100.00 | NULL  |
+----+-------------+---------+------------+------+---------------+------+---------+------+--------+----------+-------+
1 row in set, 1 warning (0.00 sec)

mysql > select count(*) from sbtest3;
+----------+
| count(*) |
+----------+
|  1000000 |
+----------+
1 row in set (0.05 sec)

mysql > show status like 'Handler_read%';
+-----------------------+-------+
| Variable_name         | Value |
+-----------------------+-------+
| Handler_read_first    | 0     |
| Handler_read_key      | 0     |
| Handler_read_last     | 0     |
| Handler_read_next     | 0     |
| Handler_read_prev     | 0     |
| Handler_read_rnd      | 0     |
| Handler_read_rnd_next | 0     |
+-----------------------+-------+
7 rows in set (0.00 sec)
```

Well, apart from observing the execution time (which is comparable to a table with the primary key), it is hard to tell as neither the status handlers don’t increment nor the `Rows_examined` information from the slow log. Moreover, global InnoDB counters, like `Innodb_rows_read`, as well as Performance Schema table statistics also do NOT change when the count is made with clustered index (explicit or implicit)!

```
mysql > CALL sys.ps_truncate_all_tables(TRUE);
(...)

mysql > select id from sbtest1 limit 1; select id from sbtest2 limit 1; select id from sbtest3 limit 1;
+--------+
| id     |
+--------+
| 731065 |
+--------+
1 row in set (0.00 sec)

+----+
| id |
+----+
|  1 |
+----+
1 row in set (0.01 sec)

+----+
| id |
+----+
|  1 |
+----+
1 row in set (0.00 sec)

mysql > select table_schema,table_name,rows_fetched from sys.schema_table_statistics where table_schema="db1";
+--------------+------------+--------------+
| table_schema | table_name | rows_fetched |
+--------------+------------+--------------+
| db1          | sbtest1    |            1 |
| db1          | sbtest2    |            1 |
| db1          | sbtest3    |            1 |
+--------------+------------+--------------+
3 rows in set (0.01 sec)

mysql > select count(*) from sbtest1; select count(*) from sbtest2; select count(*) from sbtest3;
+----------+
| count(*) |
+----------+
|  1000000 |
+----------+
1 row in set (0.21 sec)

+----------+
| count(*) |
+----------+
|  1000000 |
+----------+
1 row in set (0.03 sec)

+----------+
| count(*) |
+----------+
|  1000000 |
+----------+
1 row in set (0.03 sec)

mysql > select table_schema,table_name,rows_fetched from sys.schema_table_statistics where table_schema="db1";
+--------------+------------+--------------+
| table_schema | table_name | rows_fetched |
+--------------+------------+--------------+
| db1          | sbtest1    |      1000001 |
| db1          | sbtest2    |            1 |
| db1          | sbtest3    |            1 |
+--------------+------------+--------------+
3 rows in set (0.01 sec)
```

The select count(*) runs are clearly ignored in the above when there is no secondary key involved! Then how can we check what index was actually read during the count query execution and what amount of data had to be fetched? Well, I can think of only one way – on a freshly restarted, idle server, we can check the Buffer Pool contents (here the BP is big enough to keep whole tables and `innodb_buffer_pool_load_at_startup = OFF`).

<table style="border: 1px; border-style: solid; border-color: #000000;">
<tbody>
<tr>
<td>WARNING: the below example query may be extremely expensive on a busy production server! Therefore, it is meant only for investigation purposes on a test instance, not for regular monitoring!</td>
</tr>
</tbody>
</table>

```
mysql > select TABLE_NAME,INDEX_NAME,count(*) from INFORMATION_SCHEMA.INNODB_BUFFER_PAGE where TABLE_NAME like "`db1`.%" GROUP BY TABLE_NAME,INDEX_NAME;
Empty set (0.19 sec)

mysql > select count(*) from sbtest1; select count(*) from sbtest2; select count(*) from sbtest3;
+----------+
| count(*) |
+----------+
|  1000000 |
+----------+
1 row in set (0.22 sec)

+----------+
| count(*) |
+----------+
|  1000000 |
+----------+
1 row in set (0.20 sec)

+----------+
| count(*) |
+----------+
|  1000000 |
+----------+
1 row in set (0.87 sec)

mysql > select TABLE_NAME,INDEX_NAME,count(*) from INFORMATION_SCHEMA.INNODB_BUFFER_PAGE where TABLE_NAME like "`db1`.%" GROUP BY TABLE_NAME,INDEX_NAME;
+-----------------+-----------------+----------+
| TABLE_NAME      | INDEX_NAME      | count(*) |
+-----------------+-----------------+----------+
| `db1`.`sbtest1` | k_1             |      833 |
| `db1`.`sbtest2` | PRIMARY         |    13713 |
| `db1`.`sbtest3` | GEN_CLUST_INDEX |    14302 |
+-----------------+-----------------+----------+
3 rows in set (0.26 sec)
```

Based on the above result, we can see how many index pages were loaded to execute the count, where the small secondary index wins as it does not contain the data. In this case, it did not translate straightforwardly to the execution times, but I will not dig deeper here, as it depends on more factors, including the `innodb_parallel_read_threads`, etc.

### Another unexpected challenge after upgrading?

Has this lack of handlers, rows examined, and table statistics always impacted MySQL? Actually, no. The above results were tested with MySQL versions 8.4.3 and 8.0.40, while here is how MySQL 5.7.44 behaves with the same test tables (sbtest1 has primary and secondary key, sbtest2 has primary key only, and sbtest3 has no defined keys):

```
mysql > select table_schema,table_name,rows_fetched from sys.schema_table_statistics where table_schema="db1";
+--------------+------------+--------------+
| table_schema | table_name | rows_fetched |
+--------------+------------+--------------+
| db1          | sbtest1    |            0 |
| db1          | sbtest2    |            0 |
| db1          | sbtest3    |            0 |
+--------------+------------+--------------+
3 rows in set (0.24 sec)

mysql > flush status;
Query OK, 0 rows affected (0.00 sec)

mysql > select count(*) from sbtest1;
+----------+
| count(*) |
+----------+
|  1000000 |
+----------+
1 row in set (0.22 sec)

mysql > show status like 'Handler_read%';
+-----------------------+---------+
| Variable_name         | Value   |
+-----------------------+---------+
| Handler_read_first    | 1       |
| Handler_read_key      | 1       |
| Handler_read_last     | 0       |
| Handler_read_next     | 1000000 |
| Handler_read_prev     | 0       |
| Handler_read_rnd      | 0       |
| Handler_read_rnd_next | 0       |
+-----------------------+---------+
7 rows in set (0.01 sec)

mysql > flush status;
Query OK, 0 rows affected (0.00 sec)

mysql > select count(*) from sbtest2;
+----------+
| count(*) |
+----------+
|  1000000 |
+----------+
1 row in set (0.35 sec)

mysql > show status like 'Handler_read%';
+-----------------------+---------+
| Variable_name         | Value   |
+-----------------------+---------+
| Handler_read_first    | 1       |
| Handler_read_key      | 1       |
| Handler_read_last     | 0       |
| Handler_read_next     | 1000000 |
| Handler_read_prev     | 0       |
| Handler_read_rnd      | 0       |
| Handler_read_rnd_next | 0       |
+-----------------------+---------+
7 rows in set (0.00 sec)

mysql > flush status;
Query OK, 0 rows affected (0.00 sec)

mysql > select count(*) from sbtest3;
+----------+
| count(*) |
+----------+
|  1000000 |
+----------+
1 row in set (0.60 sec)

mysql > show status like 'Handler_read%';
+-----------------------+---------+
| Variable_name         | Value   |
+-----------------------+---------+
| Handler_read_first    | 1       |
| Handler_read_key      | 1       |
| Handler_read_last     | 0       |
| Handler_read_next     | 0       |
| Handler_read_prev     | 0       |
| Handler_read_rnd      | 0       |
| Handler_read_rnd_next | 1000001 |
+-----------------------+---------+
7 rows in set (0.01 sec)

mysql > select table_schema,table_name,rows_fetched from sys.schema_table_statistics where table_schema="db1";
+--------------+------------+--------------+
| table_schema | table_name | rows_fetched |
+--------------+------------+--------------+
| db1          | sbtest3    |      1000000 |
| db1          | sbtest2    |      1000000 |
| db1          | sbtest1    |      1000000 |
+--------------+------------+--------------+
3 rows in set (0.21 sec)
```

A careful eye will catch another surprise above – the explicit primary key uses `Handler_read_next` while the internal (hidden) cluster key uses `Handler_read_rnd_next` instead.

The slow log looks very similar in all cases:

```
# Time: 2025-01-12T17:38:09.770152Z
# User@Host: msandbox[msandbox] @ localhost []  Id:     4
# Query_time: 0.218950  Lock_time: 0.000130 Rows_sent: 1  Rows_examined: 1000000
SET timestamp=1736703489;
select count(*) from sbtest1;

# Time: 2025-01-12T17:38:44.827605Z
# User@Host: msandbox[msandbox] @ localhost []  Id:     4
# Query_time: 0.348038  Lock_time: 0.000159 Rows_sent: 1  Rows_examined: 1000000
SET timestamp=1736703524;
select count(*) from sbtest2;

# Time: 2025-01-12T17:39:01.362687Z
# User@Host: msandbox[msandbox] @ localhost []  Id:     4
# Query_time: 0.608309  Lock_time: 0.000121 Rows_sent: 1  Rows_examined: 1000000
SET timestamp=1736703541;
select count(*) from sbtest3;
```

The Innodb_rows_read status variable does increment in MySQL 5.7 as expected when reading either secondary or clustered index.

### Summary

This unexpected broken InnoDB instrumentation was reported by my colleague Iwo already in 2022: [https://bugs.mysql.com/bug.php?id=107352](https://bugs.mysql.com/bug.php?id=107352)

Sometimes new major version improvements may bring some unexpected behavior or even break important instrumentation. When analyzing query statistics in MySQL 8.0+, one may get easily confused when seeing no rows or key entries read during table counts. But it may turn out that it’s not about empty tables but rather non-working instrumentation.

![](mysql-performance-tuning-1.png)
