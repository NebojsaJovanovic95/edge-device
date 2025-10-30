/**
 * Node-RED Settings
 *
 * For more options, see https://nodered.org/docs/user-guide/runtime/configuration
 **/

module.exports = {
    // the TCP port that the Node-RED web server will listen on
    uiPort: process.env.PORT || 1880,

    // By default, Node-RED scans the ~/.node-red directory for nodes and flows
    userDir: '/data',

    // Enable logging
    logging: {
        console: {
            level: "info",
            metrics: false,
            audit: false
        }
    },

    // Admin authentication
    adminAuth: {
        type: "credentials",
        users: [{
            username: "admin",        // choose your admin username
            password: "$2b$08$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", // hashed password
            permissions: "*"
        }]
    },

    // Enable/disables the editor
    editorTheme: {
        projects: {
            enabled: true
        }
    },

    // Node-RED nodes directory
    nodesDir: '/data/nodes',

    // Optional: enable HTTPS (for edge devices on local network)
    /*
    https: {
        key: fs.readFileSync('privatekey.pem'),
        cert: fs.readFileSync('certificate.pem')
    }
    */
};
