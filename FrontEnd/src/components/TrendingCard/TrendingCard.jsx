import React from "react";
import "./TrendingCard.scss";

const TrendingCard = ({ film, index }) => {
  return (
    <div className="trending-card">
      <img src={film.img} alt={film.title} />
      <div className="card-rank">{index + 1}</div>
    </div>
  );
};

export default TrendingCard;
