import { useContext, useState } from "react";
import "./login.scss";
import { AuthContext } from "../../authContext/AuthContext";
import { login } from "../../authContext/apiCalls";
import { Link } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { error, dispatch } = useContext(AuthContext);
  const handleLogin = async (e) => {
    e.preventDefault();
    try {
     await login({ email, password }, dispatch);

      dispatch({ type: "LOGIN_SUCCESS", payload: {email, password} });
    } catch (err) {
      if (err.response && err.response.status === 404) {
        alert(err.response.data.message);
      } else {
        alert("Something went wrong!");
      }
    }
  };

  return (
    <div className="login">
      <div className="top">
        <div className="wrapper">
          <p className="logo">T3V</p>
        </div>
      </div>
      <div className="container">
        <form role="form">
          <h1>Sign In</h1>
          <input
            type="email"
            placeholder="Email of phone number"
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            type="password"
            placeholder="Password"
            onChange={(e) => setPassword(e.target.value)}
          />
          <button className="loginButton" onClick={handleLogin}>
            Sign In
          </button>
          <span className="sign-up-now">
            New to Netflix? <b>Sign up now.</b>
          </span>
          <div>
          <Link to = '/forgot-password' className="forgot-password">
            Forgot password?
          </Link>
          </div>
          <small>
            This page is protected by Google reCAPTCHA to ensure you're not a
            bot. <b>Learn more</b>.
          </small>
        </form>
      </div>
    </div>
  );
}
