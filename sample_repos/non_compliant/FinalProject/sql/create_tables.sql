-- market rate table -- bad naming: tbl_ prefix, snake_case, cryptic columns
CREATE TABLE tbl_ethanol_market_rate (
    id       INT          PRIMARY KEY,
    dt       DATE,
    val      DECIMAL(10,2),
    vol      DECIMAL(12,2)
);

-- customer table -- PII columns, still no PascalCase, tbl_ prefix
CREATE TABLE tbl_customers (
    id       INT          PRIMARY KEY,
    name     VARCHAR(100),
    email    VARCHAR(200),
    phone    VARCHAR(20),
    salary   DECIMAL(10,2)
);

-- stored procedure: sp_ prefix (forbidden), no verb other than Get,
-- joins two tables without documented grain or surrogate key
CREATE PROCEDURE sp_GetData
AS
BEGIN
    SELECT
        m.id,
        m.dt,
        m.val,
        m.vol,
        c.name,
        c.email,
        c.salary
    FROM tbl_ethanol_market_rate m
    JOIN tbl_customers c ON m.id = c.id;
END;
