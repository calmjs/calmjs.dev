'use strict';

var Logic = function(args) {
};

Logic.prototype.identity = function (i) {
    return i;
};


// lazy module definition
if ('undefined' != typeof window) {
    window.Logic = Logic;
} else {
    exports.Logic = Logic;
}
