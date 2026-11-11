---
title: "Beyond the Version Bump: Running PostgreSQL Major Upgrades in Percona Operator for PostgreSQL"
id: "2026-11-09-beyond-the-version-bump-running-postgresql-major-upgrades-in-percona-operator-for-postgresql"
date: "2026-11-09T08:06:54+00:00"
draft: false
origin: percona
description: "It was quite challenging to perform postgres major upgrade, e.g., v17 to v18, in a Percona operator/K8s environment. There was no convenient approach to accomplish this task. The only viable solutions left were a Manual Dump/Restore to a new environment or using Logical replication."
authors:
  - anil-joshi
categories:
  - "PostgreSQL"
tags:
  - "Percona Distribution for PostgreSQL"
  - "Percona Operator for PostgreSQL"
  - "Percona postgresql operator"
  - "Planet PostgreSQL"
  - "postgres major upgrade"
  - "postgres upgrade"
  - "PostgreSQL 18"
images:
  - Percona_Texture_89.jpg
slug: beyond-the-version-bump-running-postgresql-major-upgrades-in-percona-operator-for-postgresql
---

![Beyond the Version Bump: Running PostgreSQL Major Upgrades in Percona Operator for PostgreSQL](Percona_Texture_89.jpg)

It was quite challenging to perform postgres major upgrade, e.g., v17 to v18, in a Percona operator/K8s environment. There was no convenient approach to accomplish this task. The only viable solutions left were a **Manual Dump/Restore** to a new environment or using **Logical** **replication**.

But these options were not free from challenges. Procuring a new Infrastructure/Cluster or running the manual process is complex and error-prone. Logical replication has its own [caveats](https://www.postgresql.org/docs/current/logical-replication-restrictions.html); not everything can be replicated smoothly using the native logical option.

Moreover, performing a manual pg_upgrade (In-Place) in the Operator/K8S environment is risky and unsupported.

This problem was addressed effectively by our engineering team, and they released a [technical release](https://docs.percona.com/percona-operator-for-postgresql/3.0.0/ReleaseNotes/Kubernetes-Operator-for-PostgreSQL-RN2.4.0.html) of the **Major Upgrade** option under **Postgres Operator v2.4.0.** After a couple of releases, the Major Upgrade feature finally became **generally available (GA)** under operator **v2.9.0**.

- Under the hood, the major upgrade activity in the operator runs **InPlace(pg_upgrade)** triggered by the **PerconaPGUpgrade** resource.
- The Operator then pauses the cluster and shuts it down.
- The upgrade Job runs “**pg_upgrade –link”** on the primary’s volume, creating the new data directory (pg17) alongside the old one (pg16).
- Replicas are then re-synced from the upgraded primary.
- Finally, the cluster restarts on the new version.

### Minimum Requirements and Considerations

- Percona Operator for PostgreSQL v2.4.0 (**Tech Release**); however, it’s better to upgrade to v2.9.0, which is officially GA.
- If the **OS version** and **the glibc** **library** change after the upgrade, they need to be [addressed or fixed](https://docs.percona.com/percona-operator-for-postgresql/3.0.0/update-db-major.html#check-collation).
- The extensions need to be cross-validated, whether or not they are upgraded. Some extensions, such as the **pgaudit** **extension**, are not automatically upgraded. That needs to be dropped and recreated in each database where it is installed.
- The major upgrade activity invalidates (removes) any existing logical replicas that are already in place. After the upgrade, verify and [reseed](https://docs.percona.com/percona-operator-for-postgresql/3.0.0/logical-replication.html) the logical replicas.

If you are still running a pretty old Operator version, it must be upgraded to at least the latest Operator v2.4.0-1 [https://docs.percona.com/percona-operator-for-postgresql/3.0.0/update-operator.html](https://docs.percona.com/percona-operator-for-postgresql/3.0.0/update-operator.html) to avail the “**Major Upgrade”** feature.

Let’s see, step by step and in detail, how we can accomplish the major upgrade.

Existing Operator/DB Environment:

```
Operator Version: v2.4.0
Postgres Version: v16.3
```

Target Operator/DB Major Version:

```
Operator Version: v2.6.0
Postgres Version: v17.4
```

### Points to Note:

- Postgres v17 image will be available since operator v2.6.0:- [https://docs.percona.com/percona-operator-for-postgresql/latest/versions.html#versions-compatibility](https://docs.percona.com/percona-operator-for-postgresql/latest/versions.html#versions-compatibility), so we have to upgrade from any previous operator version to 2.6.0 incrementally (2.4.0 → 2.5.1 → 2.6.0).
- Since operator v2.6.0, the base OS image has changed from **ubi8** to **ubi9:** [https://perconadev.atlassian.net/browse/K8SPG-652](https://perconadev.atlassian.net/browse/K8SPG-652) & [https://docs.percona.com/percona-operator-for-postgresql/3.1.0/ReleaseNotes/Kubernetes-Operator-for-PostgreSQL-RN2.6.0.html#improvements](https://docs.percona.com/percona-operator-for-postgresql/3.1.0/ReleaseNotes/Kubernetes-Operator-for-PostgreSQL-RN2.6.0.html#improvements), which will result in a change in **the glibc** version from **v2.28** to **v2.34.** Considering this, we have to address the impact of the collation change after the upgrade: [https://docs.percona.com/percona-operator-for-postgresql/3.0.0/update-db-major.html#check-collation](https://docs.percona.com/percona-operator-for-postgresql/3.0.0/update-db-major.html#check-collation).
- The custom-built images [(https://github.com/percona/percona-docker/blob/main/postgresql-containers/README.md)](https://github.com/percona/percona-docker/blob/main/postgresql-containers/README.md) could be an option for using the existing **UBI8** images with v2.6.0 (pg17); however, that is not a recommended path and may lead to errors or failures unless thoroughly tested. The recommended approach is to switch to the supported operator version and fix the collation changes accordingly.

### Path to Operator upgrade (2.4.0 → 2.5.1 → 2.6.0)

1. We already have a running postgres setup with the details.

#### Cluster/Pod:

```
shell> kubectl get pods -n postgres-operator
NAME                                           READY   STATUS      RESTARTS   AGE
cluster1-backup-n72n-8vffx                     0/1     Completed   0          5m9s
cluster1-instance1-7gpc-0                      4/4     Running     0          6m18s
cluster1-instance1-nxcr-0                      4/4     Running     0          6m18s
cluster1-instance1-smbw-0                      4/4     Running     0          6m18s
cluster1-pgbouncer-67bdc6c664-m8x7t            2/2     Running     0          6m18s
cluster1-pgbouncer-67bdc6c664-vncf2            2/2     Running     0          6m18s
cluster1-pgbouncer-67bdc6c664-ztpg2            2/2     Running     0          6m18s
cluster1-repo-host-0                           2/2     Running     0          6m18s
percona-postgresql-operator-669bc57c58-72p9v   1/1     Running     0          6m29s
```

#### OS/Glibc:

```
sh-4.4$ cat /etc/os-release
NAME="Red Hat Enterprise Linux"
VERSION="8.10 (Ootpa)"
ID="rhel"
ID_LIKE="fedora"
VERSION_ID="8.10"
PLATFORM_ID="platform:el8"
```

```
sh-4.4$  getconf GNU_LIBC_VERSION
glibc 2.28
```

#### Important consideration:

We should always compare the **complete patch version**, as it might happen that we have the same **Major/Minor version**, say **RHEL(8.x)**; however, the **Patched version (8.x.x)** is different and ultimately affects the underlying glibc. So even if only the patch version changes, we should take it seriously and verify the collation changes and, at a minimum, rebuild the indexes: [https://docs.percona.com/percona-operator-for-postgresql/3.0.0/update-db-major.html#check-collation](https://docs.percona.com/percona-operator-for-postgresql/3.0.0/update-db-major.html#check-collation) to avoid any corruption or consistency issues.

```
sh-4.4$ rpm -q glibc
glibc-2.28-251.el8_10.2.x86_64
```

#### Database:

```
postgres=# select version();
                                                              version                                                               
------------------------------------------------------------------------------------------------------------------------------------
 PostgreSQL 16.3 - Percona Distribution on x86_64-pc-linux-gnu, compiled by gcc (GCC) 8.5.0 20210514 (Red Hat 8.5.0-20.0.3), 64-bit
(1 row)

postgres=# \d t1
                                      Table "public.t1"
   Column    |         Type          | Collation | Nullable |            Default             
-------------+-----------------------+-----------+----------+--------------------------------
 id          | bigint                |           | not null | nextval('t1_id_seq'::regclass)
 description | text                  |           | not null | 
 user_name   | character varying(64) |           |          | 
 c           | character(16)         |           |          | 
Indexes:
    "t1_pkey" PRIMARY KEY, btree (id)
    "idx_t1_user_name" btree (user_name)

postgres=# select * from t1 order by id desc limit 10;
  id  |       description        | user_name |        c         
------+--------------------------+-----------+------------------
 1000 | Testing description 1000 | USER_1000 | CHAR_1000       
  999 | Testing description 999  | USER_999  | CHAR_999        
  998 | Testing description 998  | USER_998  | CHAR_998        
  997 | Testing description 997  | USER_997  | CHAR_997        
  996 | Testing description 996  | USER_996  | CHAR_996        
  995 | Testing description 995  | USER_995  | CHAR_995        
  994 | Testing description 994  | USER_994  | CHAR_994        
  993 | Testing description 993  | USER_993  | CHAR_993        
  992 | Testing description 992  | USER_992  | CHAR_992        
  991 | Testing description 991  | USER_991  | CHAR_991        
(10 rows)
```

2. Now we will upgrade the Operator and CRD version from 2.4.0 → 2.5.1.

```
shell>  kubectl apply --server-side -f https://raw.githubusercontent.com/percona/percona-postgresql-operator/v2.5.1/deploy/crd.yaml
customresourcedefinition.apiextensions.k8s.io/crunchybridgeclusters.postgres-operator.crunchydata.com serverside-applied
customresourcedefinition.apiextensions.k8s.io/perconapgbackups.pgv2.percona.com serverside-applied
customresourcedefinition.apiextensions.k8s.io/perconapgclusters.pgv2.percona.com serverside-applied
customresourcedefinition.apiextensions.k8s.io/perconapgrestores.pgv2.percona.com serverside-applied
customresourcedefinition.apiextensions.k8s.io/perconapgupgrades.pgv2.percona.com serverside-applied
customresourcedefinition.apiextensions.k8s.io/pgadmins.postgres-operator.crunchydata.com serverside-applied
customresourcedefinition.apiextensions.k8s.io/pgupgrades.postgres-operator.crunchydata.com serverside-applied
customresourcedefinition.apiextensions.k8s.io/postgresclusters.postgres-operator.crunchydata.com serverside-applied
```

```
shell> kubectl apply --server-side -f https://raw.githubusercontent.com/percona/percona-postgresql-operator/v2.5.1/deploy/rbac.yaml -n postgres-operator
serviceaccount/percona-postgresql-operator serverside-applied
role.rbac.authorization.k8s.io/percona-postgresql-operator serverside-applied
```

```
shell> kubectl -n postgres-operator patch deployment percona-postgresql-operator \
-p'{"spec":{"template":{"spec":{"containers":[{"name":"operator","image":"docker.io/percona/percona-postgresql-operator:2.5.1"}]}}}}'
deployment.apps/percona-postgresql-operator patched
```

Once the rollout is complete, we can see the upgraded operator image to **v2.5.1**.

```
shell>kubectl rollout status deployments percona-postgresql-operator -n postgres-operator
Waiting for deployment "percona-postgresql-operator" rollout to finish: 0 of 1 updated replicas are available...
deployment "percona-postgresql-operator" successfully rolled out
```

```
shell> kubectl get deployment percona-postgresql-operator \
  -n postgres-operator \
  -o jsonpath='{.spec.template.spec.containers[*].image}{"\n"}'
docker.io/percona/percona-postgresql-operator:2.5.1
```

**Note:** The postgres pods will remain intact, as we only upgraded the operator and CRD. As we are not upgrading/patching the underlying database version at this stage, the **OS/Glibc** will also remain the same.

```
shell>kubectl get pods -n postgres-operator
NAME                                           READY   STATUS      RESTARTS   AGE
cluster1-backup-n72n-8vffx                     0/1     Completed   0          71m
cluster1-instance1-7gpc-0                      4/4     Running     0          72m
cluster1-instance1-nxcr-0                      4/4     Running     0          72m
cluster1-instance1-smbw-0                      4/4     Running     0          72m
cluster1-pgbouncer-67bdc6c664-m8x7t            2/2     Running     0          72m
cluster1-pgbouncer-67bdc6c664-vncf2            2/2     Running     0          72m
cluster1-pgbouncer-67bdc6c664-ztpg2            2/2     Running     0          72m
cluster1-repo-host-0                           2/2     Running     0          72m
percona-postgresql-operator-577645d4d5-mbn94
```

#### OS/Glibc:

```
sh-4.4$ cat /etc/os-release
NAME="Red Hat Enterprise Linux"
VERSION="8.10 (Ootpa)"
ID="rhel"
ID_LIKE="fedora"
VERSION_ID="8.10
```

```
sh-4.4$ getconf GNU_LIBC_VERSION
glibc 2.28

sh-4.4$ rpm -q glibc
glibc-2.28-251.el8_10.2.x86_64
```

3. Next, we will upgrade the Operator and CRD version from 2.5.1 → 2.6.0.

```
shell> kubectl apply --server-side -f https://raw.githubusercontent.com/percona/percona-postgresql-operator/v2.6.0/deploy/crd.yaml
customresourcedefinition.apiextensions.k8s.io/crunchybridgeclusters.postgres-operator.crunchydata.com serverside-applied
customresourcedefinition.apiextensions.k8s.io/perconapgbackups.pgv2.percona.com serverside-applied
customresourcedefinition.apiextensions.k8s.io/perconapgclusters.pgv2.percona.com serverside-applied
customresourcedefinition.apiextensions.k8s.io/perconapgrestores.pgv2.percona.com serverside-applied
customresourcedefinition.apiextensions.k8s.io/perconapgupgrades.pgv2.percona.com serverside-applied
customresourcedefinition.apiextensions.k8s.io/pgadmins.postgres-operator.crunchydata.com serverside-applied
customresourcedefinition.apiextensions.k8s.io/pgupgrades.postgres-operator.crunchydata.com serverside-applied
customresourcedefinition.apiextensions.k8s.io/postgresclusters.postgres-operator.crunchydata.com serverside-applied
```

```
shell> kubectl apply --server-side -f https://raw.githubusercontent.com/percona/percona-postgresql-operator/v2.6.0/deploy/rbac.yaml -n postgres-operator
serviceaccount/percona-postgresql-operator serverside-applied
role.rbac.authorization.k8s.io/percona-postgresql-operator serverside-applied
rolebinding.rbac.authorization.k8s.io/percona-postgresql-operator serverside-applied
```

```
shell> kubectl -n postgres-operator patch deployment percona-postgresql-operator \
-p'{"spec":{"template":{"spec":{"containers":[{"name":"operator","image":"docker.io/percona/percona-postgresql-operator:2.6.0"}]}}}}'
deployment.apps/percona-postgresql-operator patched
```

Once the rollout is complete, we can see the upgraded operator image to **v2.6.0**.

```
shell> kubectl rollout status deployments percona-postgresql-operator -n postgres-operator
deployment "percona-postgresql-operator" successfully rolled out
```

```
shell> kubectl get deployment percona-postgresql-operator \
  -n postgres-operator \
  -o jsonpath='{.spec.template.spec.containers[*].image}{"\n"}'
docker.io/percona/percona-postgresql-operator:2.6.0
```

The OS/Glibc version remains unchanged because we haven’t yet patched the database version.

```
sh-4.4$ cat /etc/os-release
NAME="Red Hat Enterprise Linux"
VERSION="8.10 (Ootpa)"
ID="rhel"
ID_LIKE="fedora"
VERSION_ID="8.10"
```

```
sh-4.4$ getconf GNU_LIBC_VERSION
glibc 2.28
```

```
sh-4.4$ rpm -q glibc
glibc-2.28-251.el8_10.2.x86_64
```

```
postgres=# select version();
                                                              version                                                               
------------------------------------------------------------------------------------------------------------------------------------
 PostgreSQL 16.3 - Percona Distribution on x86_64-pc-linux-gnu, compiled by gcc (GCC) 8.5.0 20210514 (Red Hat 8.5.0-20.0.3), 64-bit
(1 row)
```

Here, we have completed the required operator upgrade activity. We can now perform the database “**Major Upgrade**” task.

### Postgres Major Upgrade (v16 to v17)

We need to create a **PerconaPGUpgrade** **resource** (**deploy/upgrade.yaml**) by defining the source and target versions as below.

```
apiVersion: pgv2.percona.com/v2
kind: PerconaPGUpgrade
metadata:
  name: cluster1-16-to-17
spec:
  postgresClusterName: cluster1
  image: percona/percona-postgresql-operator:2.6.0-upgrade
  fromPostgresVersion: 16
  toPostgresVersion: 17
  toPostgresImage: percona/percona-postgresql-operator:2.6.0-ppg17.4-postgres
  toPgBouncerImage: percona/percona-postgresql-operator:2.6.0-ppg17.4-pgbouncer1.24.0
  toPgBackRestImage: percona/percona-postgresql-operator:2.6.0-ppg17.4-pgbackrest2.54.2
```

…

```
shell> kubectl apply -f deploy/upgrade.yaml -n postgres-operator
perconapgupgrade.pgv2.percona.com/cluster1-16-to-17 created
```

### Downtime Phase:

Once we apply the above upgrade custom resource changes, the cluster will enter a termination state, **resulting in database downtime**. During this period, all database pods will be terminated, and the application will lose connectivity to the database until the Major Upgrade is successfully completed and the cluster is back online.

```
shell> kubectl get pods -n postgres-operator
NAME                                           READY   STATUS        RESTARTS   AGE
cluster1-backup-n72n-8vffx                     0/1     Completed     0          7h35m
cluster1-repo-host-0                           0/2     Terminating   0          7h37m
percona-postgresql-operator-6c64f9b459-jwbkp   1/1     Running       0          158m
```

**Note:** The operator uses “**pg_upgrade –link”,** which avoids copying the existing database files into the new PostgreSQL data directory. Instead, it creates **hard links t**o the existing data files, significantly **reducing the time** and **additional disk space** required for a major version upgrade. This will greatly reduce downtime, especially when dealing with a large database.

During this major upgrade process, we can see new pods created to handle the upgrade, such as pg_upgrade and cleanup of old data directories.

```
cluster1-16-to-17-pgdata-*
cluster1-16-to-17-cluster1-instance1-*
```

This pod “**cluster1-16-to-17-pgdata-8mmkz**” is responsible for performing the actual upgrade of the database data directory from PostgreSQL 16 to PostgreSQL 17 using **pg_upgrade –link** and then preserving the Patroni configurations, etc.

```
NAME                                              READY   STATUS              RESTARTS   AGE
cluster1-16-to-17-pgdata-8mmkz                    0/1     Completed           0          2m21s
```

```
shell> kubectl describe pod cluster1-16-to-17-pgdata-8mmkz  -n postgres-operator

...

declare -r data_volume='/pgdata' old_version="$1" new_version="$2"
      printf 'Performing PostgreSQL upgrade from version "%s" to "%s" ...\n\n' "$@"
      gid=$(id -G); NSS_WRAPPER_GROUP=$(mktemp)
      (sed "/^postgres:x:/ d; /^[^:]*:x:${gid%% *}:/ d" /etc/group
      echo "postgres:x:${gid%% *}:") > "${NSS_WRAPPER_GROUP}"
      uid=$(id -u); NSS_WRAPPER_PASSWD=$(mktemp)
      (sed "/^postgres:x:/ d; /^[^:]*:x:${uid}:/ d" /etc/passwd
      echo "postgres:x:${uid}:${gid%% *}::${data_volume}:") > "${NSS_WRAPPER_PASSWD}"
      export LD_PRELOAD='libnss_wrapper.so' NSS_WRAPPER_GROUP NSS_WRAPPER_PASSWD
      cd /pgdata || exit
      echo -e "Step 1: Making new pgdata directory...\n"
      mkdir /pgdata/pg"${new_version}"
      echo -e "Step 2: Initializing new pgdata directory...\n"
      /usr/pgsql-"${new_version}"/bin/initdb -k -D /pgdata/pg"${new_version}"
      echo -e "\nStep 3: Setting the expected permissions on the old pgdata directory...\n"
      chmod 700 /pgdata/pg"${old_version}"
      echo -e "Step 4: Copying shared_preload_libraries setting to new postgresql.conf file...\n"
      echo "shared_preload_libraries = '$(/usr/pgsql-"""${old_version}"""/bin/postgres -D \
      /pgdata/pg"""${old_version}""" -C shared_preload_libraries)'" >> /pgdata/pg"${new_version}"/postgresql.conf
      echo -e "Step 5: Running pg_upgrade check...\n"
      time /usr/pgsql-"${new_version}"/bin/pg_upgrade --old-bindir /usr/pgsql-"${old_version}"/bin \
      --new-bindir /usr/pgsql-"${new_version}"/bin --old-datadir /pgdata/pg"${old_version}"\
       --new-datadir /pgdata/pg"${new_version}" --link --check
      echo -e "\nStep 6: Running pg_upgrade...\n"
      time /usr/pgsql-"${new_version}"/bin/pg_upgrade --old-bindir /usr/pgsql-"${old_version}"/bin \
      --new-bindir /usr/pgsql-"${new_version}"/bin --old-datadir /pgdata/pg"${old_version}" \
      --new-datadir /pgdata/pg"${new_version}" --link
      echo -e "\nStep 7: Copying patroni.dynamic.json...\n"
      cp /pgdata/pg"${old_version}"/patroni.dynamic.json /pgdata/pg"${new_version}"
      echo -e "\npg_upgrade Job Complete!"

...
```

The logs can further provide more details about each stage of the execution process.

```
shell> kubectl logs cluster1-16-to-17-pgdata-8mmkz -n postgres-operator

Step 1: Making new pgdata directory...

Step 2: Initializing new pgdata directory...

The files belonging to this database system will be owned by user "postgres".
This user must also own the server process.

The database cluster will be initialized with locale "en_US.utf-8".
The default database encoding has accordingly been set to "UTF8".
The default text search configuration will be set to "english".

Data page checksums are enabled.

fixing permissions on existing directory /pgdata/pg17 ... ok
creating subdirectories ... ok
selecting dynamic shared memory implementation ... posix
selecting default "max_connections" ... 100
selecting default "shared_buffers" ... 128MB
selecting default time zone ... UTC
creating configuration files ... ok
running bootstrap script ... ok
performing post-bootstrap initialization ... ok
syncing data to disk ... ok

initdb: warning: enabling "trust" authentication for local connections
initdb: hint: You can change this by editing pg_hba.conf or using the option -A, or --auth-local and --auth-host, the next time you run initdb.

Success. You can now start the database server using:

    /usr/pgsql-17/bin/pg_ctl -D /pgdata/pg17 -l logfile start

Step 3: Setting the expected permissions on the old pgdata directory...

Step 4: Copying shared_preload_libraries setting to new postgresql.conf file...

Step 5: Running pg_upgrade check...

...

Upgrade Complete
----------------
Optimizer statistics are not transferred by pg_upgrade.
Once you start the new server, consider running:
    /usr/pgsql-17/bin/vacuumdb --all --analyze-in-stages
Running this script will delete the old cluster's data files:
    ./delete_old_cluster.sh

real	0m7.118s
user	0m2.041s
sys	0m0.281s

Step 7: Copying patroni.dynamic.json...

pg_upgrade Job Complete!
```

Below is the individual cleanup pod created for each secondary node to remove the old postgres 16 data directory after the upgrade completes.

**Please note:** for **Primary/Leader,** there will be no cleanup pod, as the old data is still left there for recovery purposes. When we use **pg_upgrade –link,** the old data directory is not usable in the event of a rollback or recovery.

There is already a Jira ticket reported – [https://perconadev.atlassian.net/browse/K8SPG-1235-](https://perconadev.atlassian.net/browse/K8SPG-1235) to fix this behaviour and clean the old data directory once the activity is completed, to avoid any confusion. This will most likely be fixed in the next Operator release.

```
NAME                                              READY   STATUS              RESTARTS   AGE
cluster1-16-to-17-cluster1-instance1-7gpc-rnsf2   0/1     Completed           0          97s
cluster1-16-to-17-cluster1-instance1-smbw-wpxhp   0/1     Completed           0          97s
```

E.g,

```
shell>kubectl describe pod cluster1-16-to-17-cluster1-instance1-7gpc-rnsf2  -n postgres-operator

      declare -r old_version="$1"
      printf 'Removing PostgreSQL data dir for pg%s...\n\n' "$@"
      echo -e "Checking the directory exists and isn't being used...\n"
      cd /pgdata || exit
      if [ "(/usr/pgsql-"{old_version}"/bin/pg_controldata /pgdata/pg"${old_version}" | grep -c "shut down in recovery")" -ne 1 ]; then echo -e "Directory in use, cannot remove..."; exit 1; fi
      echo -e "Removing old pgdata directory...\n"
      rm -rf /pgdata/pg"oldversion""(realpath /pgdata/pg${old_version}/pg_wal)"
      echo -e "Remove Data Job Complete!"
```

```
shell> kubectl logs cluster1-16-to-17-cluster1-instance1-7gpc-rnsf2 -n postgres-operator
Removing PostgreSQL data dir for pg16...

Checking the directory exists and isn't being used...

Removing old pgdata directory...

Remove Data Job Complete!
```

Once the upgrade activity is finished on all nodes, the cluster will be back online with all existing pods.

```
shell> kubectl get pods -n postgres-operator
NAME                                              READY   STATUS      RESTARTS   AGE
cluster1-16-to-17-cluster1-instance1-7gpc-rnsf2   0/1     Completed   0          3m45s
cluster1-16-to-17-cluster1-instance1-smbw-wpxhp   0/1     Completed   0          3m45s
cluster1-16-to-17-pgdata-8mmkz                    0/1     Completed   0          4m29s
cluster1-backup-8m9c-rtvq9                        0/1     Completed   0          117s
cluster1-instance1-7gpc-0                         4/4     Running     0          118s
cluster1-instance1-nxcr-0                         4/4     Running     0          2m58s
cluster1-instance1-smbw-0                         4/4     Running     0          118s
cluster1-pgbouncer-575bbfcb64-dncw5               2/2     Running     0          2m58s
cluster1-pgbouncer-575bbfcb64-jf4ng               2/2     Running     0          2m58s
cluster1-pgbouncer-575bbfcb64-zzz7k               2/2     Running     0          2m58s
cluster1-repo-host-0                              2/2     Running     0          2m58s
percona-postgresql-operator-6c64f9b459-jwbkp      1/1     Running     0          162m
```

### Validations/Checking:

1. As we patched/upgraded the database version this time, we will now notice that the OS image and Glibc versions have changed to “**ubi9**” and “**2.34**”. That means we need to verify the [collation changes](https://docs.percona.com/percona-operator-for-postgresql/3.0.0/update-db-major.html#check-collation)and deal with them.

```
sh-5.1$ cat /etc/os-release
NAME="Red Hat Enterprise Linux"
VERSION="9.5 (Plow)"
ID="rhel"
ID_LIKE="fedora"
VERSION_ID="9.5"
```

```
sh-5.1$ getconf GNU_LIBC_VERSION
glibc 2.34
```

```
sh-5.1$ rpm -q glibc
glibc-2.34-125.el9_5.3.x86_64
```

2 . As we mentioned earlier, on all Secondary nodes, the old pg16 directory will be removed except the Leader. That was just kept there for any rollback or recovery purposes (data, WALs, etc.). Later on, you can [remove the old data](https://docs.percona.com/percona-operator-for-postgresql/3.0.0/update-db-major.html#cleanup) directory at your discretion.

cluster1-instance1-7gpc-0(Replica) :

```
sh-5.1$ ls -lh pgdata/

total 16K
drwx--S--- 19 postgres postgres 4.0K Oct 31 18:34 pg17
drwx------  4 postgres postgres 4.0K Oct 31 18:39 pg17_wal
drwxr-sr-x  3 postgres postgres 4.0K Oct 31 10:54 pgbackrest
drwxr-s---  3 postgres postgres 4.0K Oct 31 13:00 pgbackrest-spool
```

cluster1-instance1-smbw-0(Replica):

```
sh-5.1$ ls -lh pgdata/
total 16K
drwx--S--- 19 postgres postgres 4.0K Oct 31 18:34 pg17
drwx------  4 postgres postgres 4.0K Oct 31 18:39 pg17_wal
drwxr-sr-x  3 postgres postgres 4.0K Oct 31 10:54 pgbackrest
drwxr-s---  3 postgres postgres 4.0K Oct 31 13:00 pgbackrest-spool
```

cluster1-instance1-nxcr-0(Leader):

```
sh-5.1$ ls -lh pgdata/
total 36K
-rwx------  1 postgres postgres   33 Oct 31 18:31 delete_old_cluster.sh
-rw-------  1 postgres postgres   28 Oct 31 18:34 latest_commit_timestamp.txt
drwx------ 19 postgres postgres 4.0K Oct 31 18:31 pg16
drwx--S---  3 postgres postgres 4.0K Oct 31 18:31 pg16_wal
drwx------ 19 postgres postgres 4.0K Oct 31 18:33 pg17
drwx------  4 postgres postgres 4.0K Oct 31 18:39 pg17_wal
drwxr-sr-x  3 postgres postgres 4.0K Oct 31 10:54 pgbackrest
drwxr-s---  3 postgres postgres 4.0K Oct 31 12:06 pgbackrest-spool
-rw-------  1 postgres postgres  283 Oct 31 18:31 update_extensions.sql
```

```
+ Cluster: cluster1-ha (7702901380368240668) -------------------------+---------+-----------+----+-----------+
| Member                    | Host                                    | Role    | State     | TL | Lag in MB |
+---------------------------+-----------------------------------------+---------+-----------+----+-----------+
| cluster1-instance1-7gpc-0 | cluster1-instance1-7gpc-0.cluster1-pods | Replica | streaming |  2 |         0 |
| cluster1-instance1-nxcr-0 | cluster1-instance1-nxcr-0.cluster1-pods | Leader  | running   |  2 |           |
| cluster1-instance1-smbw-0 | cluster1-instance1-smbw-0.cluster1-pods | Replica | streaming |  2 |         0 |
+---------------------------+-----------------------------------------+---------+-----------+----+-----------+
```

3. Existing data and tables verification from applications or manual process to ensure no anomalies.

Now, when we access the database, we first encounter the collation change warning, as expected, since the glibc version changed from 2.28 to 2.34.

```
sh-5.1$ psql
WARNING:  database "postgres" has a collation version mismatch
DETAIL:  The database was created using collation version 2.28, but the operating system provides version 2.34.
HINT:  Rebuild all objects in this database that use the default collation and run ALTER DATABASE postgres REFRESH COLLATION VERSION, or build PostgreSQL with the right library version.
psql (17.4 - Percona Server for PostgreSQL 17.4.1)
Type "help" for help.
```

Based on the collation check below, we performed **REINDEX** on the affected single index. After that, we refreshed the collation metadata. In a complex environment with a large number of indexes, a collation change could have a greater impact and cause data corruption; [identify and fix](https://docs.percona.com/percona-operator-for-postgresql/3.0.0/update-db-major.html#check-collation)them before using the database.

```
postgres=# SELECT DISTINCT
    indrelid::regclass::text,
    indexrelid::regclass::text,
    collname,
    pg_get_indexdef(indexrelid)
FROM (
    SELECT
        indexrelid,
        indrelid,
        indcollation[i] coll
    FROM
        pg_index,
        generate_subscripts(indcollation, 1) g(i)
) s
JOIN pg_collation c ON coll = c.oid
WHERE
    collprovider IN ('d', 'c')
    AND collname NOT IN ('C', 'POSIX');
 indrelid |    indexrelid    | collname |                          pg_get_indexdef                           
----------+------------------+----------+--------------------------------------------------------------------
 t1       | idx_t1_user_name | default  | CREATE INDEX idx_t1_user_name ON public.t1 USING btree (user_name)
(1 row)
```

```
postgres=# REINDEX INDEX CONCURRENTLY  idx_t1_user_name;
REINDEX
```

```
postgres=# ALTER DATABASE postgres REFRESH COLLATION VERSION;
NOTICE:  changing version from 2.28 to 2.34
ALTER DATABASE
```

```
postgres=# select * from t1 order by id desc limit 10;

 id  |       description        | user_name |        c         
------+--------------------------+-----------+------------------
 1000 | Testing description 1000 | USER_1000 | CHAR_1000       
  999 | Testing description 999  | USER_999  | CHAR_999        
  998 | Testing description 998  | USER_998  | CHAR_998        
  997 | Testing description 997  | USER_997  | CHAR_997        
  996 | Testing description 996  | USER_996  | CHAR_996        
  995 | Testing description 995  | USER_995  | CHAR_995        
  994 | Testing description 994  | USER_994  | CHAR_994        
  993 | Testing description 993  | USER_993  | CHAR_993        
  992 | Testing description 992  | USER_992  | CHAR_992        
  991 | Testing description 991  | USER_991  | CHAR_991        
(10 rows)
```

### Production Readiness(Before you upgrade):

Although most upgrades are expected to deliver improvements, even a small number of edge cases can introduce regressions with significant business impact, including production outages. New PostgreSQL versions may also introduce behavioural changes or depreciate or remove existing features.

Therefore, for production environments, we strongly recommend at least three trial upgrade rounds, followed by thorough application validation before the final upgrade and cutover.

## Conclusion:

The PostgreSQL major upgrade process we discussed above is not limited to upgrading between consecutive major versions. We can also perform in-place upgrades across larger version gaps, such as PostgreSQL 15 to 17, provided the [applicable version compatibility](https://docs.percona.com/percona-operator-for-postgresql/latest/versions.html#versions-compatibility) requirements are met.

This feature significantly simplifies major version upgrade activities and reduces the associated operational effort. However, particularly when upgrading to Operator version 2.4.0 (where this feature was first introduced as a technical release), or when adopting it for the first time in subsequent versions, it is strongly recommended to thoroughly validate the process in a non-production or staging environment. As discussed earlier, several compatibility considerations and potential post-upgrade fixes need to be evaluated and addressed before allowing application traffic to resume in the upgraded environment.

If the upgrade fails or gets stuck for any reason, it can be resumed using the **older PostgreSQL version**: [https://docs.percona.com/percona-operator-for-postgresql/3.0.0/pause.html](https://docs.percona.com/percona-operator-for-postgresql/3.0.0/pause.html). Further, the `PerconaPGUpgrade` resource and cluster/pod-level logs (see [https://docs.percona.com/percona-operator-for-postgresql/3.0.0/update-db-major.html#troubleshooting-upgrade-issues](https://docs.percona.com/percona-operator-for-postgresql/3.0.0/update-db-major.html#troubleshooting-upgrade-issues)) can be checked to identify the issue.
