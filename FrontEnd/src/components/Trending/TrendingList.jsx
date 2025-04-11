import React, { useEffect, useRef, useState } from "react";
import TrendingCard from "../TrendingCard/TrendingCard";
import "./TrendingList.scss";
import ArrowForwardIosIcon from "@mui/icons-material/ArrowForwardIos";
import ArrowBackIosNewIcon from "@mui/icons-material/ArrowBackIosNew";
const TrendingList = ({ films }) => {
  const scrollRef = useRef();
  const [showButtons, setShowButtons] = useState(false);

  useEffect(() => {
    setShowButtons(films.length > 7);
  }, [films]);

  const scroll = (direction) => {
    const { current } = scrollRef;
    if (!current) return;
    const scrollAmout = 300;
    direction === "left"
      ? (current.scrollLeft -= scrollAmout)
      : (current.scrollLeft += scrollAmout);
  };
  return (
    <div className="trending-list">
      <h2>Hiện đang thịnh hành</h2>
      <div className="scroll-wrapper">
        {showButtons && (
          <button className="scroll-btn left" onClick={() => scroll("left")}>
            <ArrowBackIosNewIcon />
          </button>
        )}
        <div className="trending-scroll" ref={scrollRef}>
          {films.map((film, index) => (
            <TrendingCard key={film.id} film={film} index={index} />
          ))}
        </div>
        {showButtons && (
          <button className="scroll-btn right" onClick={() => scroll("right")}>
            <ArrowForwardIosIcon />
          </button>
        )}
      </div>
    </div>
  );
};

export default TrendingList;
