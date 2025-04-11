import React from "react";
import "./MovieSpecialCard.scss";
const MovieSpecialCard = ({ film, index }) => {
  return (
    <div className="movie-card">
      <div className="poster-container">
        <img src={film.img} alt={film.title} className="poster" />
      </div>

      <div className="info">
        <h3 className="rank">{index + 1}</h3>
        <div className="titles">
          <h4 className="title">{film.title}</h4>
          <p className="meta">
            {film.year} • Duration {film.limit}
          </p>
        </div>
      </div>
    </div>
  );
};

export default MovieSpecialCard;
