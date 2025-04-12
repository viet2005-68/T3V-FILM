import React, { useEffect, useState } from "react";
import "./TrendingCard.scss";
import axios from "axios";
import { Link } from "react-router-dom";
import {
  Add,
  PlayArrow,
  ThumbDownOutlined,
  ThumbUpOutlined,
} from "@mui/icons-material";

const TrendingCard = ({ filmId, index }) => {
  const [isHover, setIsHover] = useState(false);
  const [film, setFilm] = useState({});

  useEffect(() => {
    const getMovie = async () => {
      try {
        const res = await axios.get(`/api/movies/${filmId}`, {
          headers: {
            token:
              "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken,
          },
        });
        setFilm(res.data);
      } catch (err) {
        console.log(err);
      }
    };
    getMovie();
  }, [filmId]);

  return (
    <div
      className="trending-card-wrapper"
      onMouseEnter={() => setIsHover(true)}
      onMouseLeave={() => setIsHover(false)}
    >
      <Link to={{ pathname: "/watch" }} state={{ movie: film }}>
        <div className={`trending-card ${isHover ? "hovered" : ""}`}>
          <img src={film.imgSm} alt={film.title} />
          <div className="card-rank">{index + 1}</div>
          {isHover && (
            <div className="hover-trending">
              <iframe
                src={film.trailer}
                frameBorder="0"
                allow="autoplay; encrypted-media"
                allowFullScreen
                title="trailer"
              ></iframe>
              <div className="itemInfo">
                <div className="icons">
                  <PlayArrow className="icon" />
                  <Add className="icon" />
                  <ThumbUpOutlined className="icon" />
                  <ThumbDownOutlined className="icon" />
                </div>
                <div className="itemInfoTop">
                  <span className="item">{film.duration}</span>
                  <span className="limit">+{film.limit}</span>
                  <span className="item">{film.year}</span>
                  <div className="genre">{film.genre}</div>
                </div>
                <div className="desc">{film.desc}</div>
              </div>
            </div>
          )}
        </div>
      </Link>
    </div>
  );
};

export default TrendingCard;
