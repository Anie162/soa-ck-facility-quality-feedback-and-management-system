let sql = require("mssql");
let config;

if (process.env.DB_TYPE === "azure") {
  config = {
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    server: process.env.DB_SERVER,
    database: process.env.DB_NAME,
    port: parseInt(process.env.DB_PORT, 10) || 1433,
    options: {
      encrypt: true, // Azure yêu cầu TLS
      trustServerCertificate: false,
    },
  };
} else {
  sql = require("mssql/msnodesqlv8");

  if (process.env.SSMS_VERSION != 18) {
    config = {
      server: process.env.DB_SERVER,
      database: process.env.DB_NAME,
      driver: "msnodesqlv8",
      options: {
        trustedConnection: true,
        encrypt: true,
        trustServerCertificate: true,
      },
    };
  } else {
    config = {
      server: process.env.DB_SERVER,
      database: process.env.DB_NAME,
      driver: "msnodesqlv8",
      options: {
        trustedConnection: true,
        trustServerCertificate: true,
      },
    };
  }
}

const pool = new sql.ConnectionPool(config);

const connectDB = async () => {
  try {
    await pool.connect();
    console.log(
      "======================= SQL Server connected:",
      process.env.DB_TYPE || "sql"
    );

    // test query
    const result = await pool.request().query("SELECT 1 AS test");

    if (result.recordset[0]?.test === 1)
      console.log(
        "\x1b[32m%s\x1b[0m",
        "======================= Connect Database: Success"
      );
    else
      console.log(
        "\x1b[31m%s\x1b[0m",
        "======================= Connect Database: Failed"
      );
    return pool;
  } catch (err) {
    console.error("======================= Database connection failed:");
    throw err;
  }
};

module.exports = { sql, pool, connectDB };
