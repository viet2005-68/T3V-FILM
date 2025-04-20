import {useContext, useState} from "react";
import { Link } from "react-router-dom";
import { AuthContext } from "../../authContext/AuthContext";
import {forgotPassword} from "../../authContext/apiCalls.js";
import './forget.scss';
import LoadingSpinner from "../../components/LoadingSpinner/LoadingSpinner.jsx";
import { ArrowLeft } from 'lucide-react';
import { resetPassword } from "../../authContext/apiCalls.js";

const ForgotPasswordPage = () => {
    const [email, setEmail] = useState("");
    const [isSubmitted, setIsSubmitted] = useState(false);
    const {isFetching, dispatch} = useContext(AuthContext);

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
             await forgotPassword(email, dispatch);
        } catch (error) {
            console.error(error);
        }
        setIsSubmitted(true);
    };
    return (
        <div className="container">
            <div className="form-wrapper">
                <h2 className="title">Forgot Password</h2>

                {!isSubmitted ? (
                    <form className="form-content" onSubmit={handleSubmit}>
                        <p className="description">
                            Enter your email address and we will send you a link to reset your password.
                        </p>

                        <input
                            type="email"
                            placeholder="Email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            className="email-input"
                        />

                        <button
                            className="submit-button"
                            type="submit"
                            disabled={isFetching}
                        >
                            {isFetching ? <LoadingSpinner className="small-spinner"/> : "Send Reset Link"}
                        </button>

                        <div className="back-to-login-inline">
                            <Link to="/login" className="login-link">
                                <ArrowLeft className="arrow-icon"/> Back to Login
                            </Link>
                        </div>
                    </form>
                ) : (
                    <div className="submitted-message">
                        <div className="submitted-icon">
                        </div>
                        <p className="submitted-description">
                            If an account exists for {email}, you will receive a password reset link shortly.
                        </p>

                        <div className="back-to-login-inline">
                            <Link to="/login" className="login-link">
                                <ArrowLeft className="arrow-icon"/> Back to Login
                            </Link>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
export default ForgotPasswordPage;