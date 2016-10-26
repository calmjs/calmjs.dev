'use strict';

describe('Test for main for failure', function() {
    it('Main identity test for failure', function() {
        var input_value = 'A Value';
        var logic = new Logic();
        expect(logic.identity(input_value)).to.not.equal(input_value);
    });
});
