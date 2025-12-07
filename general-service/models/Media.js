const mongoose = require("mongoose");

const MediaSchema = new mongoose.Schema(
  {
    publicId: {
      type: String,
      required: true,
      unique: true,
    },
    url: {
      type: String,
      required: true,
    },
    resourceType: {
      type: String,
      enum: ["image", "video", "raw"],
      required: true,
    },
  },
  { timestamps: true }
);

module.exports = mongoose.model("Media", MediaSchema);
