const asyncHandler = require("express-async-handler");
const cloudinary = require("cloudinary").v2;
const multer = require("multer");
const Media = require("../models/Media");

// Cấu hình Cloudinary
cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET,
});

// Multer để nhận file upload
const upload = multer({ storage: multer.memoryStorage() });

const mediaService = {
  // Upload Image or Video
  UploadFile: asyncHandler(async (req, res) => {
    if (!req.file) return res.status(400).json({ message: "No file uploaded" });

    const uploadStream = cloudinary.uploader.upload_stream(
      { resource_type: "auto" },
      async (error, result) => {
        if (error) {
          console.error("Cloudinary upload error:", error);
          return res.status(500).json({ message: "Upload failed" });
        }

        // Lưu vào MongoDB
        const media = await Media.create({
          publicId: result.public_id,
          url: result.secure_url,
          resourceType: result.resource_type, // <- image | video | raw
        });

        return res.json({
          message: "File uploaded successfully",
          mediaId: media._id,
          url: media.url,
          publicId: media.publicId,
          type: media.resourceType,
        });
      }
    );

    uploadStream.end(req.file.buffer);
  }),

  // Lấy URL của file qua public ID
  GetFile: asyncHandler(async (req, res) => {
    const { mediaId } = req.params;

    const media = await Media.findById(mediaId);
    if (!media) return res.status(404).json({ message: "Media not found" });

    const url = cloudinary.url(media.publicId, {
      resource_type: media.resourceType, // image | video | raw
      secure: true,
    });

    res.json({
      message: "File fetched",
      url,
      publicId: media.publicId,
      type: media.resourceType,
    });
  }),

  // Xóa file từ Cloudinary
  DeleteFile: asyncHandler(async (req, res) => {
    const { mediaId } = req.params;

    const media = await Media.findById(mediaId);
    if (!media) return res.status(404).json({ message: "Media not found" });

    try {
      const result = await cloudinary.uploader.destroy(media.publicId, {
        resource_type: media.resourceType,
      });

      await media.deleteOne(); // xóa trên MongoDB

      res.json({
        message: "File deleted",
        cloudinary: result,
        mediaId: mediaId,
      });
    } catch (err) {
      console.error("Error deleting file:", err);
      res.status(500).json({ message: "Failed to delete file" });
    }
  }),
};

module.exports = { mediaService, upload };
