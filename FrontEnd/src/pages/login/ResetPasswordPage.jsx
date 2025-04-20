import { useState, useContext } from "react";
import { AuthContext } from "../../authContext/AuthContext";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Lock } from "lucide-react";
import LoadingSpinner from "../../components/LoadingSpinner/LoadingSpinner.jsx";
import { resetPassword } from "../../authContext/apiCalls.js";

const ResetPasswordPage = () => {
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const { error, isFetching, dispatch } = useContext(AuthContext);

    const { token } = useParams();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (password !== confirmPassword) {
            alert("Passwords do not match");
            return;
        }
        console.log(token);
        console.log(password);
        try {
            await resetPassword(token, password, dispatch);

            setTimeout(() => {
                navigate("/login");
            }, 2000);
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <div>
            <div className="container">
                <div className="form-wrapper">
                    <form className="form-content" onSubmit={handleSubmit}>
                        <h2 className="title">Reset Password</h2>

                        <input
                            type="password"
                            placeholder="New Password"
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            className="input"
                        />
                        <input
                            type="password"
                            placeholder="Confirm the password"
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            required
                            className="input"
                        />

                        <button
                            className="submit-btn"
                            type="submit"
                            disabled={isFetching}
                        >
                            {isFetching ? <LoadingSpinner className="small-spinner" /> : "Reset Password"}
                        </button>

                        <div className="back-to-login-inline">
                            <Link to="/login" className="login-link">
                                <ArrowLeft className="arrow-icon" /> Back to Login
                            </Link>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default ResetPasswordPage;