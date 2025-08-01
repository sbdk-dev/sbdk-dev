
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from "dev"."main_dbt_test__audit"."source_not_null_main_raw_events_user_id"
    
      
    ) dbt_internal_test