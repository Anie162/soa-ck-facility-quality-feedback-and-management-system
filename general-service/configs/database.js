const mongoose = require("mongoose");
const path = require("path");

const connectDB = async () => {
  try {
    const certPath = path.join(process.cwd(), process.env.TLS_CERT_KEY_FILE);

    await mongoose.connect(process.env.MONGO_URI, {
      tlsCertificateKeyFile: certPath,
    });

    console.log("======= MongoDB connected using X.509 certificate =======");
  } catch (err) {
    console.error("MongoDB connection failed:", err);
    process.exit(1);
  }
};

module.exports = { connectDB };
