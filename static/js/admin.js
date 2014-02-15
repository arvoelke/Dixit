$(document).ready(function() {
    $(adminForm).submit(function() {
        $.post($(this).attr('action'), $(this).serialize(), function(data) {
            var output = $('#adminOutput');
            output.append('<div class="stdout">' + data['stdout'] + '</div>');
            output.append('<div class="stderr">' + data['stderr'] + '</div>');
            output.animate({ scrollTop: output.prop('scrollHeight') }, "slow");
        }, 'json');
        return false;
    });
});