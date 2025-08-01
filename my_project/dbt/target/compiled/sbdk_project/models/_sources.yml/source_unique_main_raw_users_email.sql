
    
    

select
    email as unique_field,
    count(*) as n_records

from "dev"."main"."raw_users"
where email is not null
group by email
having count(*) > 1


