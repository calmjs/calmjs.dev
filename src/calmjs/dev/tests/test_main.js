'use strict';

describe('Test for main', function() {
    it('Main identity test', function() {
        var input_value = 'A Value';
        var logic = new Logic();
        expect(logic.identity(input_value)).to.equal(input_value);
    });
});
