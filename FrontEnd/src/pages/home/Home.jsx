import Featured from "../../components/featured/Featured.jsx";
import List from "../../components/list/List.jsx";
import Navbar from "../../components/navbar/Navbar.jsx";
import "./home.scss";
import { useEffect, useState } from "react";
import axios from "axios";

export default function Home({ type }) {
  const [lists, setLists] = useState([]);
  const [genre, setGenre] = useState(null);
  const [allMovie, setAllMovie] = useState([]);

  useEffect(() => {
    const getRandomLists = async () => {
      try {
        const res = await axios.get(
          `/api/lists${type ? "?type=" + type : ""}${
            genre ? "&genre=" + genre : ""
          }`,
          {
            headers: {
              token:
                "Bearer " +
                JSON.parse(localStorage.getItem("user")).accessToken,
            },
          }
        );
        setLists(res.data);
      } catch (err) {
        console.log(err);
      }
    };

    const getAllMovie = async () => {
      try {
        const res = await axios.get("/api/movies", {
          headers: {
            token:
              "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken,
          },
        });
        console.log(res.data);
        setAllMovie(res.data);
      } catch (err) {
        console.log(err);
      }
    };

    getRandomLists();
    getAllMovie();
  }, [type, genre]);
  return (
    <div className="home">
      <Navbar />
      <Featured type={type} setGenre={setGenre} />
      <List
        list={{
          title: "All Movies",
          content: allMovie.map((movie) => movie._id),
        }}
      />
      {lists.map((list) => {
        return <List list={list} />;
      })}
    </div>
  );
}
