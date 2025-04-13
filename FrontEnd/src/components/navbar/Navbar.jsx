import { ArrowDropDown, Notifications, Search } from "@mui/icons-material";
import "./navbar.scss";
import { useContext, useState } from "react";
import { Link } from "react-router-dom";
import { AuthContext } from "../../authContext/AuthContext";
import { logout } from "../../authContext/AuthActions";
import { useNavigate } from "react-router-dom";

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const { dispatch } = useContext(AuthContext);
  const [searchInput, setSearchInput] = useState("");
  const navigate = useNavigate();

  window.onscroll = () => {
    setIsScrolled(window.pageYOffset === 0 ? false : true);
    return () => (window.onscroll = null);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchInput.trim()) {
      navigate(`/search?query=${encodeURIComponent(searchInput.trim())}`);
      setSearchInput("");
    }
  };
  return (
    <div className={isScrolled ? "navbar scrolled" : "navbar"}>
      <div className="container">
        <div className="left">
          <img src="https://freeimghost.net/images/2025/04/13/favicon.png" alt="favicon" border="0" />
          <Link to="/" className="link">
            <span>Homepage</span>
          </Link>
          <Link to="/series" className="link">
            <span>Series</span>
          </Link>
          <Link to="/movies" className="link">
            <span>Movies</span>
          </Link>
          <span>New and Popular</span>
          <span>My list</span>
        </div>
        <div className="right">
          <form onSubmit={handleSearch} className="navbar-search-form">
            <input
                type="text"
                placeholder="Tìm phim..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
            />
            <button type="submit" className="search-btn">
              <Search className="icon"/>
            </button>
          </form>

          <span>KID</span>
          <Notifications className="icon"/>
          <img src={JSON.parse(localStorage.getItem("user")).profilePic}/>
          <div className="profile">
            <ArrowDropDown className="icon"/>
            <div className="options">
              <span>Settings</span>
              <span onClick={() => dispatch(logout())}>Logout</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
