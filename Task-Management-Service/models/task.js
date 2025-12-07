const mongoose = require("mongoose");

const TASK_STATUS = {
  PENDING: "PENDING",
  WAITING_MATERIAL: "WAITING_MATERIAL",
  APPROVED: "APPROVED",
  REJECTED: "REJECTED",
  PROCESSING: "PROCESSING",
  DONE: "DONE",
  SUCCESS: "SUCCESS",
  FAILED_STANDARD: "FAILED_STANDARD",
};

const StatusHistorySchema = new mongoose.Schema(
  {
    status: {
      type: String,
      enum: Object.values(TASK_STATUS),
      required: true,
    },
    note: String,
    changedBy: { type: mongoose.Schema.Types.ObjectId, ref: "User" },
    changedAt: { type: Date, default: Date.now },
  },
  { _id: false }
);

const TaskSchema = new mongoose.Schema(
  {
    reportId: { type: mongoose.Schema.Types.ObjectId, ref: "Report" },
    createdBy: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },
    assignedTo: { type: mongoose.Schema.Types.ObjectId, ref: "User" },

    title: { type: String, required: true },
    description: String,

    status: {
      type: String,
      enum: Object.values(TASK_STATUS),
      default: TASK_STATUS.PENDING,
    },

    reason: String,
    isFailedStandard: { type: Boolean, default: false },

    attachments: [{ type: mongoose.Schema.Types.ObjectId, ref: "Attachment" }],

    deadline: Date,

    statusHistory: [StatusHistorySchema],
  },
  { timestamps: true }
);

const Task = mongoose.model("Task", TaskSchema);

// QUAN TRỌNG: export theo đúng dạng object
module.exports = {
  Task,
  TASK_STATUS,
};
