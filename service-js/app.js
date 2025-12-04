require("dotenv").config();
const express = require("express");
const swaggerUi = require("swagger-ui-express");
const swaggerJsdoc = require("swagger-jsdoc");
const path = require("path");
const cors = require("cors");
const router = require("./routes/routes");
const { connectDB } = require("./configs/database");
const openurl = require("openurl");

const app = express();
const port = process.env.PORT;

app.use(cors());
app.use(express.json());

app.use(express.static(path.join(__dirname, "../frontend")));

connectDB();

// Swagger config
const swaggerOptions = {
  definition: {
    openapi: "3.0.0",
    info: {
      title: "JavaScript Service API",
      version: "1.0.0",
      description: "API documentation for the JavaScript service",
    }
  },
  // Nơi chứa các file có comment Swagger
  apis: ["./routes/*.js"],
};

// Sinh ra spec JSON
const swaggerSpec = swaggerJsdoc(swaggerOptions);

// API endpoint để merge docs
app.get("/docs-json", (req, res) => {
  res.json(swaggerSpec);
});

// Swagger UI — dùng file JSON đã merge
app.use(
  "/docs",
  swaggerUi.serve,
  swaggerUi.setup(null, {
    swaggerOptions: {
      url: "/docs-json", // load tài liệu từ endpoint merge
      defaultModelsExpandDepth: -1, // Ẩn phần Schemas
    },
    customSiteTitle: "JavaScript Service API Docs",
    customCss: `
      .swagger-ui .topbar { display: none !important; }
      .swagger-ui .topbar-wrapper .link span {
        color: #fff !important;
        font-weight: bold;
        font-size: 20px;
      }
      .swagger-ui .topbar-wrapper .link img { display: none; }
    `,
  })
);

// Routes
app.use("/api", router);

app.listen(port, async () => {
  const loginUrl = `http://localhost:${port}/login.html`;
  const jsAPIDocsUrl = `http://localhost:${port}/docs`;
  const fastApiDocsUrl = `http://localhost:8001/docs`;
  console.log(`Server is running on ${loginUrl}`);
  console.log(`Javascript API Docs is running on ${jsAPIDocsUrl}`);
  console.log(`FastAPI Docs is running on ${fastApiDocsUrl}`);

  try {
    // Mở 2 tab song song
    openurl.open(loginUrl);
    openurl.open(fastApiDocsUrl);
    openurl.open(jsAPIDocsUrl);
  } catch (err) {
    console.error("⚠️ Không mở được trình duyệt:", err.message);
  }
});
