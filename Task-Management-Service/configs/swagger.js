// Task-Management-Service/configs/swagger.js
const swaggerJsdoc = require("swagger-jsdoc");

const swaggerDefinition = {
  openapi: "3.0.0",
  info: {
    title: "Task Management Service API",
    version: "1.0.0",
    description: "API documentation for the Task Management service",
  },
};

const options = {
  swaggerDefinition,
  apis: ["./routes/**/*.js"], // đọc @openapi trong folder routes
};

const swaggerSpec = swaggerJsdoc(options);

module.exports = swaggerSpec;
