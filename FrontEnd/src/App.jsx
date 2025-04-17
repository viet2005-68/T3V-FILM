import { useContext } from "react";
import "./App.scss";
import Home from "./pages/home/Home.jsx";
import Login from "./pages/login/Login.jsx";
import Register from "./pages/register/Register.jsx";
import Watch from "./pages/watch/Watch.jsx";
import Search from "./pages/search/Search.jsx";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { AuthContext } from "./authContext/AuthContext.jsx";
import Movie from "./pages/movie/Movie.jsx";
import Chatbot from "./Chatbot/Chatbot.jsx";

function App() {
  const { user } = useContext(AuthContext);
  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={user ? <Home /> : <Navigate to="/register" />}
        />
        <Route
          path="/movies"
          element={user ? <Home type={"movie"} /> : <Navigate to="/register" />}
        />
        <Route
          path="/series"
          element={
            user ? <Home type={"series"} /> : <Navigate to="/register" />
          }
        />
        <Route
          path="/movie"
          element={user ? <Movie /> : <Navigate to="/register" />}
        ></Route>
        <Route
          path="/watch"
          element={user ? <Watch /> : <Navigate to="/register" />}
        />
        <Route path="/register" element={<Register />} />
        <Route
          path="/login"
          element={!user ? <Login /> : <Navigate to="/" />}
        />
        <Route path="/search" element={<Search/>}/>
      </Routes>
      <Chatbot />
    </Router>
  );
}

export default App;
