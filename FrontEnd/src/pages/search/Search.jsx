import Navbar from "../../components/navbar/Navbar.jsx";
import List from "../../components/List/List.jsx";
import Filter from "../../components/Filter/Filter.jsx";
import { MdManageSearch } from "react-icons/md";
import {Grid, TablePagination} from "@mui/material";
import {useEffect, useState} from "react";
import axios from "axios";
import "./search.scss"

function Header({query}){
    return (
        <div className="row-header">
            <div className="icon">
                <MdManageSearch size={40} color="white" />
            </div>
            <h3 className="category-name">
                Kết quả tìm kiếm "{query || "Tất cả"}"
            </h3>
        </div>
    );
}
function Tab() {
    return (<div className="row-tabs-container">
        <a className="active">Phim</a>
        <a>Diễn viên</a>
    </div>)
}


export default function Search({type}) {
    const [query, setQuery] = useState("");
    const [lists, setLists] = useState([]);
    const [genre, setGenre] = useState(null);
    const [allMovie, setAllMovie] = useState([]);
    const [page, setPage] = useState(2);
    const [rowsPerPage, setRowsPerPage] = useState(10);

    const moviesPerPage = 8;

    useEffect(() => {
        const getRandomLists = async () => {
            try {
                const res = await axios.get(`/api/lists${type ? "?type=" + type : ""}${genre ? "&genre=" + genre : ""}`, {
                    headers: {
                        token: "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken,
                    },
                });
                setLists(res.data);
            } catch (err) {
                console.log(err);
            }
        };

        const getAllMovie = async () => {
            try {
                const res = await axios.get("/api/movies", {
                    headers: {
                        token: "Bearer " + JSON.parse(localStorage.getItem("user")).accessToken,
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
    const handleChangePage = (event, newPage) => {
        setPage(newPage);
    };

    const handleChangeRowsPerPage = (event) => {
        setRowsPerPage(parseInt(event.target.value, 10));
        setPage(0);
    };
    return (<div className="search">

        <div className="search-content">
            <Header query={query}/>
            <Tab/>
            <div className="tab-content">
                <Filter/>
                <Grid container spacing={2}>
                    {allMovie
                        .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                        .map((movie) => (
                            <Grid item xs={12} sm={6} md={3} key={movie._id}>
                                <div className="movie-card">
                                    <img src={movie.imgSm} alt={movie.title} />
                                    <h4>{movie.title}</h4>
                                </div>
                            </Grid>
                        ))}
                </Grid>

                <List
                    list={{
                        title: "All Movies",
                        content: allMovie.map((movie) => movie._id),
                    }}
                />
                <TablePagination className="pagination"
                                 component="div"
                                 count={100}
                                 page={page}
                                 onPageChange={handleChangePage}
                                 rowsPerPage={rowsPerPage}
                                 onRowsPerPageChange={handleChangeRowsPerPage}
                                 sx={{
                                     color: "white",            // Màu chữ chính
                                     '.MuiTablePagination-selectLabel, .MuiTablePagination-displayedRows': {
                                         color: 'white',          // Label và số trang
                                     }, '.MuiSvgIcon-root': {
                                         color: 'white',          // Icon mũi tên
                                     },
                                 }}
                />
            </div>
        </div>
    </div>);
}