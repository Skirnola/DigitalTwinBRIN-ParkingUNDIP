class User {
    constructor(username, email, password, idWorker) {
        this.username = username;
        this.email = email;
        this.password = password;
        this.idWorker = idWorker;
    }
}

class AuthSystem {
    constructor() {
        this.users = JSON.parse(localStorage.getItem('users')) || [];
    }

    register(username, email, password, idWorker) {
        const userExists = this.users.some(user => user.email === email);
        if (userExists) {
            throw new Error('User already exists!');
        }
        const user = new User(username, email, password, idWorker);
        this.users.push(user);
        localStorage.setItem('users', JSON.stringify(this.users));
        return user;
    }

    login(email, password) {
        const user = this.users.find(u => u.email === email && u.password === password);
        if (user) {
            return user;
        }
        throw new Error('Invalid email or password!');
    }
}

const auth = new AuthSystem();