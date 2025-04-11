const router = require("express").Router();
const Movie = require("../models/Movie");
const verify = require("../verifyToken");
const reviewRoute = require('./reviews');

router.use('/reviews', reviewRoute)

//CREATE
router.post("/", verify, async (req, res) => {
    if (req.user.isAdmin) {
        const newMovie = new Movie(req.body);
        try {
            const savedMovie = await newMovie.save();
            res.status(200).json(savedMovie);
        }
        catch (err) {
            res.status(500).json(err);
        }
    }
    else {
        res.status(403).json("You are not allowed to create movie!");
    }
})

//UPDATE
router.put("/:id", verify, async (req, res) => {
    if (req.user.isAdmin) {
        try {
            const updatedMovie = await Movie.findByIdAndUpdate(req.params.id, { $set: req.body }, { new: true });
            res.status(200).json(updatedMovie);
        }
        catch (err) {
            res.status(500).json(err);
        }
    }
    else {
        res.status(403).json("You are not allowed to update movie!");
    }
})

//DELETE
router.delete("/:id", verify, async (req, res) => {
    if (req.user.isAdmin) {
        try {
            await Movie.findByIdAndDelete(req.params.id);
            res.status(200).json("Delete movie successfully");
        }
        catch (err) {
            res.status(500).json(err);
        }
    }
    else {
        res.status(403).json("You are not allowed to delete movie!");
    }
})

//GET RANDOM (1 Movie)
router.get("/random", verify, async (req, res) => {
    const type = req.query.type;
    let movie;
    try {
        if (type === 'series') {
            movie = await Movie.aggregate([
                { $match: { isSeries: true } },
                { $sample: { size: 1 } }
            ]);
        }
        else if (type === 'movie') {
            movie = await Movie.aggregate([
                { $match: { isSeries: false } },
                { $sample: { size: 1 } }
            ]);
        }
        else {
            movie = await Movie.aggregate([
                { $sample: { size: 1 } }
            ]);
        }
        res.status(200).json(movie);
    }
    catch (err) {
        res.status(500).json(err);
    }
})

// GET TOP MOVIES
router.get("/top", async (req, res) => {
    try {
        const topMovies = await Movie.aggregate([
            {
                $addFields: {
                    avgRating: {
                        $cond: [
                            { $gt: [{ $size: '$reviews' }, 0] },
                            { $avg: '$reviews.rating' },
                            0
                        ]
                    }
                }
            },
            { $sort: { avgRating: -1 } },
            { $limit: 10 }
        ])
        res.status(200).json(topMovies)
    }
    catch (err) {
        res.status(500).json(err)
    }
})

//GET 1 movie by ID
router.get("/:id", verify, async (req, res) => {
    try {
        const movie = await Movie.findById(req.params.id);
        res.status(200).json(movie);
    }
    catch (err) {
        res.status(500).json(err);
    }
})

//GET ALL 
// To get all movies: call /api/movies/
// To get movies filtered by genre: call /api/movies?genre=YOUR_MOVIE_GENRE
// To get movies filtered by title: call /api/movies?title=YOUR_MOVIE_NAME
// To get movies filtered by year: call /api/movies?year=YOUR_MOVIE_YEAR
router.get("/", verify, async (req, res) => {
    const filter = {}
    if (req.query.genre) {
        filter.genre = req.query.genre
    }
    if (req.query.title) {
        filter.title = { $regex: req.query.title, $options: "i" }
    }
    if (req.query.year) {
        filter.year = req.query.year
    }
    try {
        const movies = await Movie.find(filter).populate("reviews.user", "username profilePic")
        res.status(200).json(movies.reverse())
    }
    catch (err) {
        res.status(500).json(err);
    }
})

module.exports = router;