import "./moviecard.scss";
import { useRef, useState, useEffect } from "react";
import axios from "axios";
import Button from "@mui/material/Button";
import FavoriteIcon from "@mui/icons-material/Favorite";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import InfoIcon from "@mui/icons-material/Info";
function handlePopup(card) {
  const popup = card.querySelector(".movie-popup");
  const rect = popup.getBoundingClientRect();
  const padding = 16;

  // Reset transform trước để đo chính xác
  popup.style.transform = "translateX(0)";

  const overflowRight = rect.right - window.innerWidth + padding;
  const overflowLeft = rect.left - padding;

  if (overflowRight > 0) {
    popup.style.transform = `translateX(-${overflowRight}px)`;
  } else if (overflowLeft < 0) {
    popup.style.transform = `translateX(${Math.abs(overflowLeft)}px)`;
  }
}

function Popup({ movie }) {
  const cardRef = useRef();

  const onHover = () => {
    handlePopup(cardRef.current);
  };
  return (
    <div className="movie-popup">
      <div className="popup-poster-wrapper">
        <img
          className="popup-poster"
          src={movie.imgSm}
          alt={movie.title}
        />
      </div>

      <div className="popup-info">
        <h3>{movie.title}</h3>

        <div className="popup-buttons">
          {/*<button className="watch">Xem ngay</button>
        <button className="like">Thích</button>
        <button className="info">Chi tiết</button>*/}
          <Button
            className="watch-btn"
            size="small"
            color="red"
            startIcon={<PlayArrowIcon fontSize="inherit" />}
          >
            Xem ngay
          </Button>

          <Button
            className="like"
            variant="outlined"
            size="small"
            color="neutral"
            startIcon={<FavoriteIcon fontSize="inherit" />}
          >
            Thích
          </Button>
          <Button
            className="info"
            variant="outlined"
            size="small"
            color="neutral"
            startIcon={<InfoIcon fontSize="inherit" />}
          >
            Chi tiết
          </Button>
        </div>

        <div className="popup-meta">
          <span className="item">{movie.duration}</span>
          <span className="limit">+{movie.limit}</span>
          <span className="item">{movie.year}</span>
          <div className="genre">{movie.genre}</div>
          <span>HD</span>
        </div>
      </div>
    </div>
  );
}

export default function MovieCard({movieId, index}) {
  const [movie, setMovie] = useState({});

  useEffect(() => {
    const getMovie = async () => {
      try {
        const res = await axios.get(`/api/movies/${movieId}`, {
          headers: {
            token:
                "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken,
          },
        });
        setMovie(res.data);
      }
      catch (error) {
        console.log(error);
      }
    };
    getMovie();
  }, [movieId]);
  return (
    <div className="movie-card-wrapper">
      <div className="movie-card">
        <img
          className="movie-thumbnail"
          src={movie.imgSm}
          alt={movie.title}
        />
        <h3>{movie.title}</h3>
      </div>
      <Popup movie={movie} />
    </div>
  );
}
