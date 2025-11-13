-- Connect to the 'booklatte' database to ensure tables are created in the correct place.
\c booklatte;

-- Result Tables for Advanced Analytics
CREATE TABLE IF NOT EXISTS holtwinters_results_all (
    date DATE,
    bundle_units NUMERIC,
    antecedent_units NUMERIC,
    consequent_units NUMERIC,
    bundle_units_forecast NUMERIC,
    bundle_units_adjusted_forecast NUMERIC,
    antecedent_units_forecast NUMERIC,
    antecedent_units_after_cannibalization NUMERIC,
    consequent_units_forecast NUMERIC,
    consequent_units_after_cannibalization NUMERIC,
    bundle_row INTEGER,
    bundle_id VARCHAR(16),
    category VARCHAR(32)
);

CREATE TABLE IF NOT EXISTS association_rules (
    bundle_id VARCHAR(16) PRIMARY KEY,
    antecedents_names VARCHAR(128),
    consequents_names VARCHAR(128),
    support NUMERIC,
    confidence NUMERIC,
    lift NUMERIC,
    leverage NUMERIC,
    conviction NUMERIC,
    combined_score NUMERIC,
    category VARCHAR(32)
);

CREATE TABLE IF NOT EXISTS ped_summary (
    bundle_id VARCHAR(16) PRIMARY KEY,
    category VARCHAR(32),
    rule_row INTEGER,
    product_id_1 VARCHAR(32),
    product_id_2 VARCHAR(32),
    product_name_1 VARCHAR(128),
    product_name_2 VARCHAR(128),
    mode VARCHAR(32),
    n_price_points INTEGER,
    elasticity_epsilon NUMERIC,
    intercept_logk NUMERIC,
    r2_logspace NUMERIC
);

CREATE TABLE IF NOT EXISTS nlp_optimization_results (
    bundle_id VARCHAR(16) PRIMARY KEY,
    bundle_name VARCHAR(255),
    category VARCHAR(32),
    product_a VARCHAR(255),
    product_b VARCHAR(255),
    product_a_price NUMERIC(10, 2),
    product_b_price NUMERIC(10, 2),
    current_price_total NUMERIC(10, 2),
    product_a_cogs NUMERIC(10, 2),
    product_b_cogs NUMERIC(10, 2),
    cogs_total NUMERIC(10, 2),
    elasticity_epsilon NUMERIC,
    base_demand_k NUMERIC,
    r_squared NUMERIC,
    n_points INTEGER,
    bundle_price_recommended NUMERIC(10, 2),
    quantity_demanded NUMERIC,
    profit NUMERIC(12, 2),
    price_cap NUMERIC(10, 2),
    min_discount_pct NUMERIC(5, 2),
    optimization_success BOOLEAN
);