(sbdk-dev) mattstrautmann@MacBookPro my_analytics_project % sbdk start
🚀 Running initial pipeline...
🏃‍♂️ Running users pipeline...
📊 Generated 10000 user records
📈 Users Pipeline Results:
    - Total users: 10,000
    - Countries: 195
    - Active users: 8,536 (85.4%)
    - Date range: 2023-08-02 12:36:41.012045 to 2025-08-01 22:45:41.290687
    
✅ Users pipeline completed successfully!

🏃‍♂️ Running events pipeline...
📊 Generated 50000 event records
📈 Events Pipeline Results:
    - Total events: 50,000
    - Unique users: 9,753
    - Event types: 13
    - Purchases: 445
    - Total revenue: $114,279.31
    - Date range: 2025-05-04 00:03:30.184383 to 2025-08-02 00:00:33.062957

    Top Event Types:
    - page_view: 19,093 (38.2%)
    - click: 12,075 (24.2%)
    - scroll: 7,353 (14.7%)
    - login: 3,908 (7.8%)
    - add_to_cart: 1,878 (3.8%)
✅ Events pipeline completed successfully!

🏃‍♂️ Running orders pipeline...
📊 Generated 20000 order records
📈 Orders Pipeline Results:
    - Total orders: 20,000
    - Unique customers: 7,914
    - Completed orders: 15,988 (79.9%)
    - Cancelled orders: 987 (4.9%)
    - Total revenue: $4,776,786.03
    - Average order value: $298.77
    - Recurring orders: 7,030 (35.1%)
    - Date range: 2024-08-10 02:31:47.538623 to 2025-08-01 23:58:04.172231

    Top Categories by Revenue:
    - consulting: 2,520 orders, $2,262,247.73 (avg: $1123.82)
    - training: 2,478 orders, $1,110,253.10 (avg: $553.47)
    - support: 2,501 orders, $546,979.53 (avg: $273.22)
    - upgrade: 2,433 orders, $307,279.87 (avg: $159.96)
    - enterprise_addon: 2,532 orders, $224,219.02 (avg: $110.94)

    Payment Method Distribution:
    - credit_card: 9,560 orders (47.8%)
    - paypal: 3,196 orders (16.0%)
    - stripe: 1,894 orders (9.5%)
    - bank_transfer: 849 orders (4.2%)
    - crypto: 322 orders (1.6%)
    - wire: 167 orders (0.8%)
✅ Orders pipeline completed successfully!

  ✅ Pipelines complete           ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✅ dbt transformations complete ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
╭──────────────────────────────────────── ✅ Pipeline Complete ─────────────────────────────────────────╮
│ 🎉 Development pipeline completed successfully!                                                       │
│                                                                                                       │
│ Data available in: data/my_analytics_project.duckdb                                                   │
│ Query your data: duckdb data/my_analytics_project.duckdb                                              │
│                                                                                                       │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────╯
✅ Initial pipeline completed successfully
👀 Watching: pipelines
👀 Watching: dbt/models
╭───────────────────────────────────────── 🚀 SBDK Dev Server ──────────────────────────────────────────╮
│ 🎉 Development server started!                                                                        │
│                                                                                                       │
│ Watching paths: pipelines, dbt/models                                                                 │
│ Database: data/my_analytics_project.duckdb                                                            │
│                                                                                                       │
│ Press Ctrl+C to stop                                                                                  │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────╯
              🚀 SBDK Development Server               
              🚀 SBDK Development Server               
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component    ┃ Status    ┃ Details                  ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ File Watcher │ 🟢 Active │ Monitoring for changes   │
               🚀 SBDK Development Server               
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component    ┃ Status     ┃ Details                  ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ File Watcher │ 🟢 Active  │ Monitoring for changes   │
│ DuckDB       │ 🟢 Ready   │ Local database available │
│ dbt          │ 🟢 Ready   │ Transform models loaded  │
│ Pipeline     │ 🟡 Running │ Last run: In progress    │
│ Time         │ 🕰️ Active   │ 00:04:03                 │
🏃‍♂️ Running users pipeline...
               🚀 SBDK Development Server               
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component    ┃ Status     ┃ Details                  ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ File Watcher │ 🟢 Active  │ Monitoring for changes   │
│ DuckDB       │ 🟢 Ready   │ Local database available │
│ dbt          │ 🟢 Ready   │ Transform models loaded  │
│ Pipeline     │ 🟡 Running │ Last run: In progress    │
│ Time         │ 🕰️ Active   │ 00:04:16                 │
🏃‍♂️ Running events pipeline...
📊 Generated 50000 event records
📈 Events Pipeline Results:
    - Total events: 50,000
    - Unique users: 9,760
    - Event types: 13
    - Purchases: 265
    - Total revenue: $69,534.92
    - Date range: 2025-05-04 00:09:50.023387 to 2025-08-02 00:02:44.564194
               🚀 SBDK Development Server               
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component    ┃ Status     ┃ Details                  ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ File Watcher │ 🟢 Active  │ Monitoring for changes   │
│ DuckDB       │ 🟢 Ready   │ Local database available │
│ dbt          │ 🟢 Ready   │ Transform models loaded  │
│ Pipeline     │ 🟡 Running │ Last run: In progress    │
│ Time         │ 🕰️ Active   │ 00:04:19                 │
🏃‍♂️ Running orders pipeline...
📊 Generated 20000 order records
📈 Orders Pipeline Results:
    - Total orders: 20,000
    - Unique customers: 7,887
    - Completed orders: 16,006 (80.0%)
    - Cancelled orders: 1,011 (5.1%)
    - Total revenue: $4,834,625.32
    - Average order value: $302.05
    - Recurring orders: 7,022 (35.1%)
    - Date range: 2024-08-14 03:30:06.466035 to 2025-08-02 00:02:52.577103

    Top Categories by Revenue:
    - consulting: 2,587 orders, $2,302,284.93 (avg: $1121.97)
    - training: 2,495 orders, $1,098,586.03 (avg: $551.78)
    - support: 2,492 orders, $557,035.13 (avg: $277.82)
    - upgrade: 2,494 orders, $320,512.82 (avg: $161.96)
    - enterprise_addon: 2,580 orders, $232,343.69 (avg: $112.41)

    Payment Method Distribution:
               🚀 SBDK Development Server               
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component    ┃ Status     ┃ Details                  ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ File Watcher │ 🟢 Active  │ Monitoring for changes   │
│ DuckDB       │ 🟢 Ready   │ Local database available │
│ dbt          │ 🟢 Ready   │ Transform models loaded  │
│ Pipeline     │ 🟡 Running │ Last run: In progress    │
  ✅ Pipelines complete           ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✅ dbt transformations complete ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
╭──────────────────────────────────────── ✅ Pipeline Complete ─────────────────────────────────────────╮
│ 🎉 Development pipeline completed successfully!                                                       │
│                                                                                                       │
               🚀 SBDK Development Server               
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component    ┃ Status     ┃ Details                  ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ File Watcher │ 🟢 Active  │ Monitoring for changes   │
│ DuckDB       │ 🟢 Ready   │ Local database available │
│ dbt          │ 🟢 Ready   │ Transform models loaded  │
│ Pipeline     │ 🟡 Running │ Last run: In progress    │
│ Time         │ 🕰️ Active   │ 00:04:28                 │
🏃‍♂️ Running users pipeline...
               🚀 SBDK Development Server               
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component    ┃ Status     ┃ Details                  ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ File Watcher │ 🟢 Active  │ Monitoring for changes   │
│ DuckDB       │ 🟢 Ready   │ Local database available │
│ dbt          │ 🟢 Ready   │ Transform models loaded  │
│ Pipeline     │ 🟡 Running │ Last run: In progress    │
│ Time         │ 🕰️ Active   │ 00:04:40                 │
🏃‍♂️ Running events pipeline...
📊 Generated 50000 event records
📈 Events Pipeline Results:
    - Total events: 50,000
    - Unique users: 9,773
    - Event types: 13
    - Purchases: 269
    - Total revenue: $71,515.61
    - Date range: 2025-05-04 00:08:28.638438 to 2025-08-02 00:03:56.945401
               🚀 SBDK Development Server               
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component    ┃ Status     ┃ Details                  ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ File Watcher │ 🟢 Active  │ Monitoring for changes   │
│ DuckDB       │ 🟢 Ready   │ Local database available │
│ dbt          │ 🟢 Ready   │ Transform models loaded  │
│ Pipeline     │ 🟡 Running │ Last run: In progress    │
│ Time         │ 🕰️ Active   │ 00:04:43                 │
🏃‍♂️ Running orders pipeline...
📊 Generated 20000 order records
📈 Orders Pipeline Results:
    - Total orders: 20,000
    - Unique customers: 7,908
    - Completed orders: 15,886 (79.4%)
    - Cancelled orders: 1,056 (5.3%)
    - Total revenue: $4,774,963.44
    - Average order value: $300.58
    - Recurring orders: 6,935 (34.7%)
    - Date range: 2024-08-30 21:09:38.345555 to 2025-08-02 00:00:24.774502

    Top Categories by Revenue:
    - consulting: 2,528 orders, $2,248,981.73 (avg: $1105.15)
    - training: 2,480 orders, $1,093,548.11 (avg: $556.8)
    - support: 2,538 orders, $565,577.71 (avg: $280.41)
    - upgrade: 2,558 orders, $331,586.85 (avg: $161.91)
    - enterprise_addon: 2,428 orders, $214,753.69 (avg: $112.14)

    Payment Method Distribution:
               🚀 SBDK Development Server               
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component    ┃ Status     ┃ Details                  ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ File Watcher │ 🟢 Active  │ Monitoring for changes   │
│ DuckDB       │ 🟢 Ready   │ Local database available │
│ dbt          │ 🟢 Ready   │ Transform models loaded  │
│ Pipeline     │ 🟡 Running │ Last run: In progress    │
  ✅ Pipelines complete           ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
               🚀 SBDK Development Server               
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component    ┃ Status     ┃ Details                  ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ File Watcher │ 🟢 Active  │ Monitoring for changes   │
│ DuckDB       │ 🟢 Ready   │ Local database available │
│ dbt          │ 🟢 Ready   │ Transform models loaded  │
│ Pipeline     │ 🟢 Success │ Last run: 00:04:48       │
│ Time         │ 🕰️ Active   │ 00:04:56                 │
└──────────────┴────────────┴──────────────────────────┘