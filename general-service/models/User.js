const mongoose = require("mongoose");
const { v4: uuidv4 } = require("uuid");

const userSchema = new mongoose.Schema(
  {
    UserID: { type: String, default: uuidv4 },
    UserFullName: { type: String, required: true },
    UserEmail: { type: String, required: true, unique: true },
    UserPhone: { type: String, required: true },
    UserPassword: { type: String, required: true },
    UserBalance: { type: Number, default: 0 },
  },
  { versionKey: false }
);

// =============================
// Static methods (giữ API giống SQL Server version)
// =============================
userSchema.statics.findByEmail = function (email) {
  return this.findOne({ UserEmail: email });
};

userSchema.statics.findById = function (id) {
  return this.findOne({ UserID: id });
};

userSchema.statics.createUser = async function ({
  fullName,
  phone,
  email,
  password,
  balance = 0,
}) {
  const user = new this({
    UserFullName: fullName,
    UserPhone: phone,
    UserEmail: email,
    UserPassword: password,
    UserBalance: balance,
  });

  await user.save();
  return user.UserID;
};

userSchema.statics.updatePassword = function (email, hashedPassword) {
  return this.updateOne(
    { UserEmail: email },
    { UserPassword: hashedPassword }
  );
};

userSchema.statics.withdraw = function (id, amount) {
  return this.updateOne(
    { UserID: id },
    { $inc: { UserBalance: -amount } }
  );
};

userSchema.statics.deposit = function (id, amount) {
  return this.updateOne(
    { UserID: id },
    { $inc: { UserBalance: amount } }
  );
};

userSchema.statics.getBalance = async function (id) {
  const user = await this.findOne({ UserID: id });
  return user ? user.UserBalance : null;
};

module.exports = mongoose.model("User", userSchema);
