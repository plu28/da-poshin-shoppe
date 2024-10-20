-- cart potions
create table
  public.cart_potions (
    id bigint generated by default as identity not null,
    cart_id integer not null,
    sku text not null,
    quantity integer null,
    constraint cart_potions_pkey primary key (id),
    constraint cart_potions_cart_id_key unique (cart_id),
    constraint cart_potions_cart_id_fkey foreign key (cart_id) references carts (cart_id),
    constraint cart_potions_sku_fkey foreign key (sku) references catalog (sku)
  ) tablespace pg_default;

-- carts
create table
  public.carts (
    id bigint generated by default as identity not null,
    red_ml bigint not null default '0'::bigint,
    green_ml bigint not null default '0'::bigint,
    blue_ml bigint not null default '0'::bigint,
    dark_ml bigint not null default '0'::bigint,
    potion_quantity integer not null default 0,
    cart_id integer not null,
    constraint carts_pkey primary key (id),
    constraint carts_cart_id_key unique (cart_id),
    constraint carts_id_key unique (id)
  ) tablespace pg_default;

-- catalog
create table
  public.catalog (
    sku text not null,
    quantity bigint not null default '0'::bigint,
    name text not null,
    price integer not null default 50,
    id integer generated by default as identity not null,
    potion_type integer[] not null default '{0,0,0,0}'::integer[],
    constraint catalog_pkey primary key (id),
    constraint catalog_id_key unique (id),
    constraint catalog_sku_key unique (sku)
  ) tablespace pg_default;

-- global inventory
create table
  public.global_inventory (
    green_ml bigint not null default '0'::bigint,
    gold bigint not null default '0'::bigint,
    id integer generated by default as identity not null,
    red_ml bigint not null default '0'::bigint,
    blue_ml bigint not null default '0'::bigint,
    dark_ml bigint not null default '0'::bigint,
    constraint global_inventory_pkey primary key (id),
    constraint global_inventory_id_key unique (id)
  ) tablespace pg_default;

-- roxanne (collects what roxanne is selling)
create table
  public.roxanne (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone not null default now(),
    sku text null,
    ml_per_barrel bigint null,
    price integer null,
    quantity integer null,
    potion_type integer[] null,
    constraint roxanne_pkey primary key (id)
  ) tablespace pg_default;

-- customers (tracking what customers visit my shop)
create table
  public.customers (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone not null default now(),
    customer_name text null default ''::text,
    character_class text null,
    level integer null,
    visit_count integer not null default 0,
    constraint customers_pkey primary key (id)
  ) tablespace pg_default;

-- logs (tracking every endpoint call)
create table
  public.logs (
    id bigint generated by default as identity not null,
    endpoint text null,
    request json null,
    response json null,
    created_at timestamp with time zone null default (now() at time zone 'pst'::text),
    constraint logs_pkey primary key (id)
  ) tablespace pg_default;

-- strategy (the potions I want to be able to sell)
create table
  public.strategy (
    id bigint generated by default as identity not null,
    sku text null,
    quantity bigint not null default '0'::bigint,
    constraint strategy_pkey primary key (id),
    constraint strategy_sku_key unique (sku)
  ) tablespace pg_default;
