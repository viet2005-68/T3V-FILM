import "./moviecard.scss";
import { useRef } from "react";
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
          src={`https://image.tmdb.org/t/p/w500${movie.backdrop_path}`}
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
          <span>IMDb {movie.vote_average}</span>
          <span>{movie.release_date?.slice(0, 4)}</span>
          <span>HD</span>
        </div>
      </div>
    </div>
  );
}

export default function MovieCard({ movie }) {
  return (
    <div className="movie-card-wrapper">
      <div className="movie-card">
        <img
          className="movie-thumbnail"
          src={`https://image.tmdb.org/t/p/w500${movie.poster_path}`}
          alt={movie.title}
        />
        <h3>{movie.title}</h3>
      </div>
      <Popup movie={movie} />
    </div>
  );
}
