export const loginStart = () => ({
  type: "LOGIN_START",
});

export const loginSuccess = (user) => ({
  type: "LOGIN_SUCCESS",
  payload: user,
});

export const loginFailure = () => ({
  type: "LOGIN_FAILURE",
});

// Logout
export const logout = () => ({
  type: "LOGOUT",
});
export const verifyEmailStart = () => ({
  type: "VERIFY_EMAIL_START",
});

export const verifyEmailSuccess = (user) => ({
  type: "VERIFY_EMAIL_SUCCESS",
  payload: user,
});

export const verifyEmailFailure = () => ({
  type: "VERIFY_EMAIL_FAILURE",
});

export const forgetEmailStart = () => ({
  type: "FORGET_EMAIL_START",
});
export const forgetEmailFailure = () => ({
  type: "FORGET_EMAIL_FAILURE",
});
export const forgetEmailSuccess = () => ({
  type: "FORGET_EMAIL_SUCCESS",
});

export const resetPasswordSuccess = () => ({
  type: "RESET_PASSWORD_SUCCESS",
});

export const resetPasswordFailure = () => ({
  type: "RESET_PASSWORD_FAILURE",
});

export const resetPasswordStart = () => ({
  type: "RESET_PASSWORD_START",
});