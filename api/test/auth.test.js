const chai = require("chai");
const chaiHttp = require("chai-http");
const app = require('../../api/index'); // Thay bằng đường dẫn đến ứng dụng của bạn
const User = require("../src/models/User");
const should = chai.should();

chai.use(chaiHttp);

describe("Auth API", () => {
    // Test đăng ký người dùng
    describe("POST /api/auth/register", () => {
        it("should register a new user successfully", (done) => {
            const user = {
                username: "testUser",
                email: "test@example.com",
                password: "testPassword"
            };

            chai.request(app)
                .post("/api/auth/register")
                .send(user)
                .end((err, res) => {
                    res.should.have.status(201);
                    res.body.should.have.property("_id");
                    res.body.should.have.property("username").eql("testUser");
                    res.body.should.have.property("email").eql("test@example.com");
                    done();
                });
        });

        it("should return 400 if missing fields", (done) => {
            const user = {
                email: "test@example.com",
                password: "testPassword"
            };

            chai.request(app)
                .post("/api/auth/register")
                .send(user)
                .end((err, res) => {
                    res.should.have.status(400);
                    res.body.should.have.property("message").eql("All fields are required");
                    done();
                });
        });
    });

    // Test đăng nhập
    describe("POST /api/auth/login", () => {
        it("should login successfully and return access token", (done) => {
            const user = {
                email: "test@example.com",
                password: "testPassword"
            };

            chai.request(app)
                .post("/api/auth/login")
                .send(user)
                .end((err, res) => {
                    res.should.have.status(200);
                    res.body.should.have.property("accessToken");
                    res.body.should.have.property("username").eql("testUser");
                    res.body.should.have.property("email").eql("test@example.com");
                    done();
                });
        });

        it("should return 404 with wrong password", (done) => {
            const user = {
                email: "test@example.com",
                password: "wrongPassword"
            };

            chai.request(app)
                .post("/api/auth/login")
                .send(user)
                .end((err, res) => {
                    res.should.have.status(404);
                    res.body.should.eql("Wrong password or username!");
                    done();
                });
        });

        it("should return 404 for non-existent user", (done) => {
            const user = {
                email: "nonexistent@example.com",
                password: "testPassword"
            };

            chai.request(app)
                .post("/api/auth/login")
                .send(user)
                .end((err, res) => {
                    res.should.have.status(404);
                    res.body.should.eql("Wrong password or username!");
                    done();
                });
        });
    });
});
