
    
    

select
    email as unique_field,
    count(*) as n_records

from "demo_project"."raw"."users"
where email is not null
group by email
having count(*) > 1


