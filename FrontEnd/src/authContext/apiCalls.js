import axios from "axios"
import {loginStart, loginFailure, loginSuccess, verifyEmailSuccess} from "./AuthActions"


export const login = async (user, dispatch) => {
    dispatch(loginStart());
    try {
        const res = await axios.post("/api/auth/login", user);
        dispatch(loginSuccess(res.data));
    }
    catch (err) {
        console.log(err);
        dispatch(loginFailure())
    }
};

export const verifyEmail = async (code, dispatch, navigate) => {
    dispatch({ type: "VERIFY_EMAIL_START" });

    try {
        console.log("Mã xác thực:", code);
        const res = await axios.post("/api/auth/verify-email", {
            code: code,
        }, {
            headers: {
                "Content-Type": "application/json"
            }
        });

        alert("Email verified successfully");

        // Điều hướng về trang login sau khi xác minh email
       // navigate("/signin");

        dispatch({ type: "VERIFY_EMAIL_SUCCESS", payload: res.data });
    } catch (error) {
        dispatch({ type: "VERIFY_EMAIL_FAILURE" });
        throw error;
    }
};

export const forgotPassword = async (email, dispatch)  => {
    dispatch({ type: "FORGET_EMAIL_START" });
    try {
        const response = await axios.post("/api/auth/forgot-password", {email});
        dispatch({ type: "VERIFY_EMAIL_SUCCESS", payload: response.data });
    } catch (error) {
        dispatch({ type: "FORGET_EMAIL_FAILURE" });
        throw error;
    }
}

export const resetPassword = async (token, password, dispatch) => {
    dispatch({ type: "RESET_PASSWORD_START" });
    try {
        const response = await axios.post(  `/api/auth/reset-password/${token}`
            , { password });
        dispatch({ type: "RESET_PASSWORD_SUCCESS", payload: response.data });
    } catch (error) {
        dispatch({ type: "RESET_PASSWORD_FAILURE" });
        throw error;
    }
}