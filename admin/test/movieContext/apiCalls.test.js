/* eslint-env mocha */
global.localStorage = {
    getItem: (key) => {
        if (key === "user") {
            return JSON.stringify({ accessToken: "test-token" });
        }
        return null;
    },
    setItem: () => {},
    removeItem: () => {},
    clear: () => {},
};

import { expect } from "chai";
import sinon from "sinon";
import axios from "axios";

import {
    getMovies,
    createMovie,
    updateMovie,
    deleteMovie,
} from "../../src/context/movieContext/apiCalls.js";

describe("apiCalls", () => {
    let dispatch;
    let axiosGetStub, axiosPostStub, axiosPutStub, axiosDeleteStub;
    let user;

    beforeEach(() => {
        dispatch = sinon.spy();
        user = { accessToken: "test-token" };
        localStorage.setItem("user", JSON.stringify(user));

        axiosGetStub = sinon.stub(axios, "get");
        axiosPostStub = sinon.stub(axios, "post");
        axiosPutStub = sinon.stub(axios, "put");
        axiosDeleteStub = sinon.stub(axios, "delete");
    });

    afterEach(() => {
        sinon.restore();
        localStorage.clear();
    });

    describe("getMovies", () => {
        it("should dispatch success on API success", async () => {
            const mockMovies = [{ title: "Movie 1" }];
            axiosGetStub.resolves({ data: mockMovies });

            await getMovies(dispatch);

            expect(dispatch.firstCall.args[0].type).to.equal("GET_MOVIES_START");
            expect(dispatch.secondCall.args[0].type).to.equal("GET_MOVIES_SUCCESS");
            expect(dispatch.secondCall.args[0].payload).to.deep.equal(mockMovies);
        });

        it("should dispatch failure on API error", async () => {
            axiosGetStub.rejects(new Error("Failed"));

            await getMovies(dispatch);

            expect(dispatch.firstCall.args[0].type).to.equal("GET_MOVIES_START");
            expect(dispatch.secondCall.args[0].type).to.equal("GET_MOVIES_FAILURE");
        });
    });

    describe("createMovie", () => {
        it("should dispatch success on API success", async () => {
            const newMovie = { title: "New Movie" };
            axiosPostStub.resolves({ data: newMovie });

            await createMovie(newMovie, dispatch);

            expect(dispatch.firstCall.args[0].type).to.equal("CREATE_MOVIE_START");
            expect(dispatch.secondCall.args[0].type).to.equal("CREATE_MOVIE_SUCCESS");
            expect(dispatch.secondCall.args[0].payload).to.deep.equal(newMovie);
        });

        it("should dispatch failure on API error", async () => {
            const newMovie = { title: "New Movie" };
            axiosPostStub.rejects(new Error("Failed"));

            await createMovie(newMovie, dispatch);

            expect(dispatch.firstCall.args[0].type).to.equal("CREATE_MOVIE_START");
            expect(dispatch.secondCall.args[0].type).to.equal("CREATE_MOVIE_FAILURE");
        });
    });

    describe("updateMovie", () => {
        it("should dispatch success on API success", async () => {
            const updatedMovie = { _id: "123", title: "Updated Movie" };
            axiosPutStub.resolves({ data: updatedMovie });

            await updateMovie(updatedMovie, dispatch);

            expect(dispatch.firstCall.args[0].type).to.equal("UPDATE_MOVIE_START");
            expect(dispatch.secondCall.args[0].type).to.equal("UPDATE_MOVIE_SUCCESS");
            expect(dispatch.secondCall.args[0].payload).to.deep.equal(updatedMovie);
        });

        it("should dispatch failure on API error", async () => {
            const updatedMovie = { _id: "123", title: "Updated Movie" };
            axiosPutStub.rejects(new Error("Failed"));

            await updateMovie(updatedMovie, dispatch);

            expect(dispatch.firstCall.args[0].type).to.equal("UPDATE_MOVIE_START");
            expect(dispatch.secondCall.args[0].type).to.equal("UPDATE_MOVIE_FAILURE");
        });
    });

    describe("deleteMovie", () => {
        it("should dispatch success on API success", async () => {
            axiosDeleteStub.resolves();

            await deleteMovie("123", dispatch);

            expect(dispatch.firstCall.args[0].type).to.equal("DELETE_MOVIE_START");
            expect(dispatch.secondCall.args[0].type).to.equal("DELETE_MOVIE_SUCCESS");
            expect(dispatch.secondCall.args[0].payload).to.equal("123");
        });

        it("should dispatch failure on API error", async () => {
            axiosDeleteStub.rejects(new Error("Failed"));

            await deleteMovie("123", dispatch);

            expect(dispatch.firstCall.args[0].type).to.equal("DELETE_MOVIE_START");
            expect(dispatch.secondCall.args[0].type).to.equal("DELETE_MOVIE_FAILURE");
        });
    });
});
