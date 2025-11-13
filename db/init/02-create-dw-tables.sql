-- Connect to the 'booklatte' database to ensure tables are created in the correct place.
\c booklatte;

-- Dimensions
CREATE TABLE IF NOT EXISTS current_product_dimension (
    product_id VARCHAR(64) PRIMARY KEY,
    product_name VARCHAR(255),
    price NUMERIC(10,2),
    product_cost NUMERIC(10,2),
    last_transaction_datetime TIMESTAMP,
    record_version INTEGER,
    is_current BOOLEAN,
    parent_sku VARCHAR(255),
    category VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS history_product_dimension (
    product_id VARCHAR(64),
    product_name VARCHAR(255),
    price NUMERIC(10,2),
    product_cost NUMERIC(10,2),
    last_transaction_datetime TIMESTAMP,
    record_version INTEGER,
    is_current BOOLEAN,
    parent_sku VARCHAR(255),
    category VARCHAR(64),
    PRIMARY KEY (product_id, record_version)
);

CREATE TABLE IF NOT EXISTS time_dimension (
    time_id VARCHAR(32) PRIMARY KEY,
    time_desc VARCHAR(255),
    time_level INTEGER,
    parent_id VARCHAR(32)
);

-- Market Basket Analysis Tables
CREATE TABLE IF NOT EXISTS transaction_records (
    receipt_no INTEGER PRIMARY KEY NOT NULL,
    sku TEXT
);

--Fact Tables   
CREATE TABLE IF NOT EXISTS fact_transaction_dimension (
    date DATE,
    time_id VARCHAR(32),
    receipt_no INTEGER,
    product_id VARCHAR(64),
    product_name VARCHAR(255),
    qty INTEGER,
    price NUMERIC(10,2),
    line_total NUMERIC(12,2),
    net_total NUMERIC(12,2),
    discount NUMERIC(12,2),
    evat NUMERIC(12,2),
    pwd NUMERIC(12,2),
    senior NUMERIC(12,2),
    tax NUMERIC(12,2),
    total_gross NUMERIC(12,2),
    void INTEGER,
    base_qty INTEGER,
    take_out VARCHAR(10),
    PRIMARY KEY (receipt_no, date, product_id),
    FOREIGN KEY (product_id) REFERENCES current_product_dimension(product_id)
);