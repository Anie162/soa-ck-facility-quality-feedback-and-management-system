// Task-Management-Service/configs/db.js
const mongoose = require("mongoose");

const connectDB = async () => {
  try {
    if (!process.env.MONGO_URI) {
      throw new Error("MONGO_URI is not defined in .env");
    }

    const conn = await mongoose.connect(process.env.MONGO_URI);

    console.log(
      "======= Task-Management-Service: MongoDB connected =======",
      conn.connection.host
    );
  } catch (error) {
    console.error("Task-Management-Service: MongoDB connection error:", error);
    process.exit(1);
  }
};

module.exports = connectDB;
