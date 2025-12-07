// Task-Management-Service/services/task.js
const { Task, TASK_STATUS } = require("../models/task");

const CreateTask = async (req, res) => {
  try {
    const { reportId, assignedTo, title, description, deadline, createdBy } =
      req.body;

    // sau này bạn có thể lấy createdBy từ req.user._id nếu có auth
    const creatorId = createdBy;

    const task = await Task.create({
      reportId,
      createdBy: creatorId,
      assignedTo,
      title,
      description,
      deadline,
      statusHistory: [
        {
          status: TASK_STATUS.PENDING,
          note: "Task created",
          changedBy: creatorId,
        },
      ],
    });

    return res.status(201).json(task);
  } catch (error) {
    console.error("CreateTask error:", error);
    return res
      .status(500)
      .json({ message: "Tạo task thất bại", error: error.message });
  }
};

const GetTasks = async (req, res) => {
  try {
    const { status, assignedTo, createdBy } = req.query;

    const query = {};
    if (status) query.status = status;
    if (assignedTo) query.assignedTo = assignedTo;
    if (createdBy) query.createdBy = createdBy;

    // BỎ populate đi, chỉ find plain thôi
    const tasks = await Task.find(query);

    return res.status(200).json(tasks);
  } catch (error) {
    console.error("GetTasks error:", error);
    return res
      .status(500)
      .json({ message: "Lấy danh sách task thất bại", error: error.message });
  }
};


const GetTaskById = async (req, res) => {
  try {
    const { id } = req.params;

    // BỎ populate
    const task = await Task.findById(id);

    if (!task) {
      return res.status(404).json({ message: "Không tìm thấy task" });
    }

    return res.status(200).json(task);
  } catch (error) {
    console.error("GetTaskById error:", error);
    return res
      .status(500)
      .json({ message: "Lấy task thất bại", error: error.message });
  }
};


const UpdateTask = async (req, res) => {
  try {
    const { id } = req.params;
    const { title, description, assignedTo, deadline } = req.body;

    const task = await Task.findByIdAndUpdate(
      id,
      { title, description, assignedTo, deadline },
      { new: true }
    );

    if (!task) {
      return res.status(404).json({ message: "Không tìm thấy task" });
    }

    return res.status(200).json(task);
  } catch (error) {
    console.error("UpdateTask error:", error);
    return res
      .status(500)
      .json({ message: "Cập nhật task thất bại", error: error.message });
  }
};

const UpdateTaskStatus = async (req, res) => {
  try {
    const { id } = req.params;
    const { status, reason, isFailedStandard, changedBy } = req.body;

    if (!Object.values(TASK_STATUS).includes(status)) {
      return res.status(400).json({ message: "Trạng thái không hợp lệ" });
    }

    const task = await Task.findById(id);
    if (!task) {
      return res.status(404).json({ message: "Không tìm thấy task" });
    }

    task.status = status;
    if (reason) task.reason = reason;
    if (typeof isFailedStandard === "boolean") {
      task.isFailedStandard = isFailedStandard;
    }

    task.statusHistory.push({
      status,
      note: reason,
      changedBy,
    });

    await task.save();

    return res.status(200).json(task);
  } catch (error) {
    console.error("UpdateTaskStatus error:", error);
    return res
      .status(500)
      .json({ message: "Cập nhật trạng thái thất bại", error: error.message });
  }
};

module.exports = {
  CreateTask,
  GetTasks,
  GetTaskById,
  UpdateTask,
  UpdateTaskStatus,
};
