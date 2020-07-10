// Static constants
var TITLE = '{{ display.Labels.TITLE }}';
var ALERT_TITLE = TITLE + ' (!)';


// Refresh each element every X millesconds
var GAMELIST_INTERVAL = 10000;
var USERLIST_INTERVAL = 20000;
var CHATROOM_INTERVAL = 3000;
var GAMEBOARD_INTERVAL = 4000;


// Summary of game state for an observer
var observerMessages = [];
observerMessages[{{ states.BEGIN }}] = 'Join the game!';
observerMessages[{{ states.CLUE }}] = 'Creating a clue';
observerMessages[{{ states.PLAY }}] = 'Playing cards';
observerMessages[{{ states.VOTE }}] = 'Voting';
observerMessages[{{ states.END }}] = 'Game over';


// Summary of game state for a player who can take an action
var actionMessages = [];
actionMessages[{{ states.BEGIN }}] = 'Start the game once you have all players.';
actionMessages[{{ states.CLUE }}] = 'Create a clue.<br />You can show/hide your hand at the bottom.';
actionMessages[{{ states.PLAY }}] = 'Select the best card for the following clue.';
actionMessages[{{ states.VOTE }}] = 'Vote for the card you think was selected by the clue maker, given their clue.';
actionMessages[{{ states.END }}] = 'Play again?';


// Summary of game state for a player who needs to wait
var waitingMessages = [];
waitingMessages[{{ states.BEGIN }}] = 'Waiting for more players ...';
waitingMessages[{{ states.CLUE }}] = 'Waiting for a clue to be made ...';
waitingMessages[{{ states.PLAY }}] = 'Waiting for other players to select a card ...';
waitingMessages[{{ states.VOTE }}] = 'Waiting for other players to vote ...';
waitingMessages[{{ states.END }}] = 'Waiting for the next game ...';


// Bunny status icons to display beside names and games
function pluralize(x) {
    return x != 1 ? 's' : '';
};
function activityIcon(rel_last_active) {
    minutes = Math.floor(rel_last_active / 60);
    hours = Math.floor(minutes / 60);
    days = Math.floor(hours / 24);
    if (minutes == 0) {
        var activity = 'Active right now';
        var status = '{{ display.Images.ICON_ACTIVE }}';
    } else if (hours == 0) {
        activity = 'Last active ' + minutes + ' minute' + pluralize(minutes) + ' ago';
        status = '{{ display.Images.ICON_AWAY }}';
    } else if (days == 0) {
        activity = 'Last active ' + hours + ' hour' + pluralize(hours) + ' ago';
        status = '{{ display.Images.ICON_ASLEEP }}';
    } else {
        activity = 'Away for ' + days + ' day' + pluralize(days);
        status = '{{ display.Images.ICON_ASLEEP }}';
    }
    return '<img src="' + status + '" title="' + activity + '" />';
}


// Rendering plain text in HTML (with smilies.js)
function smilify(text) {
    return smilifyText(text, '{{ display.WebPaths.SMILIES }}');
};


// All of the jQuery stuff
$(document).ready(function() {
    // Global state
    var activeGame = $.url().fparam('gid');  // id of currently selected game
    var handHash = undefined;  // hash of most recently rendered hand, or undefined
    var cardsHash = undefined;  // hash of most recently rendered current cards, or undefined
    var votesHash = undefined;  // hash of most recently revealed votes, or undefined
    var lastChatUpdate = 0;  // timestamp of most recently retrieved message


    // Periodic Game List Polling
    var gameListWorker = function worker() {
        $.getJSON('getgames', function(data) {
            var html = [];
            if (data.length > 0) {
                html.push('<tr><th>&nbsp;</th><th>Host</th><th>Name</th><th>State</th><th>Players</th><th>Score</th><th>Cards</th></tr>');
            }
            $.each(data, function(i, game) {
                html.push('<tr class="' + (game.gid == activeGame ? 'activeGame' : 'visibleGame') + '">');
                html.push('<td class="firstCell">' + activityIcon(game.relLastActive) + '</td>');
                html.push('<td><input type="hidden" name="gid" value="' + game.gid + '" />'
                        + smilify(game.host) + '</td>');
                html.push('<td>' + smilify(game.name) + '</td>');
                html.push('<td>' + observerMessages[game.state] + '</td>');
                html.push('<td title="' + textToHtml(game.players.join(', ')) + '">'
                        + game.players.length
                        + (game.state == {{ states.BEGIN }} ? ' / ' + game.maxPlayers : '') + '</td>');
                html.push('<td>' + game.topScore + (game.maxScore ? ' / ' + game.maxScore : '') + '</td>');
                html.push('<td class="lastCell" title="' + game.deckName + '">'
                        + game.left + ' / ' + game.size + '</td>');
                html.push('</tr>');
            });
            $('#gameTable').html(html.join(''));

            // Register handlers for elements that have been added dynamically
            $('#gameTable button').button();
            $('.visibleGame').click(function(e) {
                gid = $(this).find('input').val();
                switchGame(gid);
                e.preventDefault();
            });
        }).always(function() {
            setTimeout(gameListWorker, GAMELIST_INTERVAL);
        });
    };
    gameListWorker();
    function refreshGameList() {
        setTimeout(gameListWorker, 0);
    };


    // Periodic User List Polling
    var userListWorker = function worker() {
        $.getJSON('getusers', function(data) {
            var html = [];
            $.each(data, function(i, user) {
                html.push('<tr>');
                html.push('<td class="bunnyIcon">' + activityIcon(user.relLastActive) + '</td>');
                html.push('<td>' + smilify(user.name) + '</td>');
                html.push('</tr>');
            });
            $('#userTable').html(html.join(''));
        }).always(function() {
            setTimeout(userListWorker, USERLIST_INTERVAL);
        });
    };
    userListWorker();
    function refreshUserList() {
        setTimeout(userListWorker, 0);
    };


    // Periodic Chat Room Polling
    function formatHours(i) {
        return (i + 11) % 12 + 1;
    }
    function formatMinutes(i) {
        return i < 10 ? '0' + i : i;
    }
    function formatAmPm(i) {
        return i >= 12 ? 'pm' : 'am';
    }
    function addMessage(obj) {
        var date = new Date(obj.t * 1000);
        $('#chatLog').append('<p><span class="chatTime">('
                           + formatHours(date.getHours()) + ':' + formatMinutes(date.getMinutes()) + formatAmPm(date.getHours())
                           + ')</span> <span class="chatUser">' + smilify(obj.user) + '</span>: '
                           + '<span class="chatText" id="' + obj.mid + '"></span></p>');
        $('#' + obj.mid).html(smilify(obj.msg));
    };
    var chatRoomWorker = function worker() {
        $.getJSON('chat?t=' + lastChatUpdate, function(data) {
            chatLog = $('#chatLog');
            wasFullyScrolled = (chatLog.prop('scrollHeight') <= chatLog.prop('scrollTop') + chatLog.height() + 20);  // 20 padding

            $.each(data.log, function(i, obj) {
                if (obj.t > lastChatUpdate) {
                    addMessage(obj);
                }
            });
            lastChatUpdate = data.t;

            if (data.log.length > 0 && wasFullyScrolled) {
                $('#chatLog').animate({ scrollTop: chatLog.prop('scrollHeight') }, "slow");
                if (!document.hasFocus()) {
                    document.title = ALERT_TITLE;
                }
            }
        }).always(function() {
            setTimeout(chatRoomWorker, CHATROOM_INTERVAL);
        });
    };
    chatRoomWorker();
    $('#sendMsg').submit(function (e) {
        if ($('#chatInput').val().length > 0) {
            $.post('chat', $(this).serialize(), function(data) {
                setTimeout(chatRoomWorker, 0);
            });
        }
        $('#chatInput').val('');
        e.preventDefault();
    });
    $('#chatInput').click(function() {
        if ($(this).val() == '{{ display.Labels.DEFAULT_TEXT }}') {
            $(this).select();
        }
    });


    // Periodic Game Board Polling
    var gameBoardWorker = function worker() {
        if (document.hasFocus()) {
            document.title = TITLE;
        }
        if (activeGame === undefined) {
            return;
        }
        sendCommand({{ commands.GET_BOARD }}, null, function(data) {
            var numPlayers = data.order.length;
            var clueMaker = data.order[data.turn];

            // Colour picker / game joiner
            if (data.state == {{ states.BEGIN }} && numPlayers < data.maxPlayers) {
                $('#bunnyPalette').show();
                $('.joinGame').addClass('clickable').removeClass('bunnyTaken');
                $.each(data.colours, function(uid, colour) {
                    $('#' + colour).removeClass('clickable').addClass('bunnyTaken');
                });
            } else {
                $('#bunnyPalette').hide();
            }

            // Determine highest rank
            var maxRank = 0;
            $.each(data.ranked, function(puid, rank) {
                if (rank > maxRank) {
                    maxRank = rank;
                }
            });

            // Scoreboard
            var scoreBoard = [];
            $.each(data.order, function(i, puid) {
                // Determine if a winner
                var isWinner = (data.state == {{ states.END }} && data.ranked[puid] == maxRank);

                // Indicate who's clue it is
                scoreBoard.push('<tr>');
                scoreBoard.push('<td>' + (i == data.turn && data.state != {{ states.BEGIN }}
                                       ? '<img src="{{ display.Images.YOUR_TURN }}" width="{{ display.Sizes.YOUR_TURN }}" title="Story Teller" />'
                                       : '&nbsp;') + '</td>');

                // Name of player and option to kick them if host
                var canKick = data.isHost
                           && (data.state == {{ states.BEGIN }} || numPlayers > {{ limits.min_players }})
                           && data.state != {{ states.PLAY }}
                           && data.state != {{ states.VOTE }};
                scoreBoard.push('<td class="player">'
                              + (canKick ? '[<a class="kickPlayer" href="#" title="Kick Player" id="' + puid + '">x</a>] ' : '')
                              + '<span style="' + (puid == data.user ? 'font-weight:bold' : '') + '">'
                              + smilify(data.players[puid]) + '</span></td>');

                // Action that player has taken pertaining to the current game state
                extra = '&nbsp;';
                if (data.requiresAction[puid]) {
                    extra = '<img class="thinking" src="{{ display.Images.THINKING }}" title="Thinking" />';
                } else if (data.state == {{ states.PLAY }}) {
                    extra = '<img src="{{ display.Images.CARD_BACK }}" title="Selected card" />';
                } else if (data.state == {{ states.VOTE }}) {
                    extra = '<img src="{{ display.Images.VOTE_TOKEN }}" title="Voted" />';
                }
                scoreBoard.push('<td><div class="userAction">' + extra + '</div></td>');

                // Spacers to order player by rank
                scoreBoard.push('<td><div style="width:40px">&nbsp;</div></td>');
                scoreBoard.push(Array(data.ranked[puid] + 1).join('<td>&nbsp;</td>'));

                // Player's bunny piece and score
                scoreBoard.push('<td class="bunnyPiece"><div style="background-color: #' + data.colours[puid]
                              + '" title="' + textToHtml(data.players[puid]) + '"><img src="'
                              + ((data.state == {{ states.BEGIN }} || data.state == {{ states.END }})
                               ? '{{ display.Images.BUNNY_READY }}' : '{{ display.Images.BUNNY_RUN }}')
                              + '" /></div></td>');
                scoreBoard.push('<td class="score">' + data.scores[puid] + '</td>');

                // Spacers to make every row have the same number of cells
                scoreBoard.push(Array(maxRank - data.ranked[puid] + 1).join('<td>&nbsp;</td>'));

                // Number of points accumulated this round
                scoreBoard.push('<td class="lastScore">'
                              + (data.round.scores[puid] ? '(+' + data.round.scores[puid] + ')' : '&nbsp;')
                              + '</td>');

                // Add trophy if winner
                scoreBoard.push('<td>' + (isWinner ? smilify('(winner)') : '&nbsp;') + '</td>');

                // Space the rest
                scoreBoard.push('<td style="width:100%">&nbsp;</td>');
                scoreBoard.push('</tr>');
            });
            $('#scoreBoard').html(scoreBoard.join('')).toggle(numPlayers > 0);
            $('.kickPlayer').click(kickPlayer);  // since element was dynamically generated

            // State-dependent display / options
            if (!data.isPlayer) {
                $('#gameState').html(observerMessages[data.state]);
            } else if (data.requiresAction[data.user]) {
                $('#gameState').html(actionMessages[data.state]);
                if (!document.hasFocus()) {
                    document.title = ALERT_TITLE;
                }
            } else {
                $('#gameState').html(waitingMessages[data.state]);
            }
            $('#joinGame').toggle();
            $('#startGame').toggle(data.state == {{ states.BEGIN }} && data.isHost
                                && numPlayers >= {{ limits.min_players }});

            // Game configuration dependent stuff
            $('#clueTextarea').attr('maxlength', data.maxClueLength);

            // Current Clue
            if (data.round.clue !== undefined) {
                $('#clue').html('Clue: "' + smilify(data.round.clue) + '"').fadeIn();
            } else {
                $('#clue').hide();
            }

            // Render hand if changed
            if (data.player.handHash != handHash) {
                handHash = data.player.handHash;
                updateCards(data.player.hand, '#hand');
                $('#handContainer').toggle(data.player.hand !== undefined);
            }

            // Render current cards if changed
            if (data.round.cardsHash != cardsHash) {
                cardsHash = data.round.cardsHash;
                updateCards(data.round.cards, '#cards');

                // Toggle hand for convenience
                if (data.round.cards !== undefined && data.state != {{ states.CLUE }}) {
                    setHandHidden();
                } else if (data.round.cards === undefined && data.state == {{ states.PLAY }}
                         && data.user != clueMaker) {
                    setHandShown();
                }
            }

            // Render most recent votes if changed
            if (data.round.votesHash != votesHash) {
                votesHash = data.round.votesHash;
                if (data.round.cards !== undefined) {
                    $.each(data.round.votes, function(puid, cid) {
                        var card = $('#' + cid);
                        var randomLeft = Math.ceil(card.position().left + Math.random() * {{ display.Sizes.CARD_WIDTH - display.Sizes.TOKEN }});
                        var randomTop = Math.ceil(card.offset().top + Math.random() * {{ display.Sizes.CARD_HEIGHT - display.Sizes.TOKEN }});
                        card.append('<div class="token" title="' + textToHtml(data.players[puid])
                                  + '" style="left:' + randomLeft + 'px;top:' + randomTop
                                  + 'px;background-color:#' + data.colours[puid] + '">&nbsp;</div>');
                    });
                    $('.token').fadeIn();
                    $.each(data.round.owners, function(puid, cid) {
                        var card = $('#' + cid);
                        card.css({'background-color' : '#' + data.colours[puid],
                                  'border-color' : '#' + data.colours[puid]});
                        if (puid != data.round.clueMaker) {
                            card.find('.small').fadeTo(400, 0.1);
                        }
                        card.attr('title', data.players[puid]);
                    });
                }
            }

            // Bind/unbind state-dependent click handlers to all cards
            if (data.state == {{ states.CLUE }} && clueMaker == data.user) {
                $('#cards .card').unbind('click').removeClass('clickable');
                $('#hand .card').click(setupActionFormHandler({{ commands.CREATE_CLUE }})).addClass('clickable');
            } else if (data.state == {{ states.PLAY }} && data.requiresAction[data.user]) {
                $('#cards .card').unbind('click').removeClass('clickable');
                $('#hand .card').click(setupActionFormHandler({{ commands.PLAY_CARD }})).addClass('clickable');
            } else if (data.state == {{ states.VOTE }} && data.requiresAction[data.user]) {
                $('#hand .card').unbind('click').removeClass('clickable');
                $('#cards .card').click(setupActionFormHandler({{ commands.CAST_VOTE }})).addClass('clickable');
            } else {
                $('.card').unbind('click').removeClass('clickable');
            }
        }).always(function() {
            setTimeout(gameBoardWorker, GAMEBOARD_INTERVAL);
        });
    };
    gameBoardWorker();
    function refreshGameBoard() {
        setTimeout(gameBoardWorker, 0);
    };


    // Change either the current cards or the user's hand
    function cardCell(card, hack) {
        return '<div class="card magnifier" id="' + card.cid + '" hack="' + hack + '">'
              + '<img class="small" src="' + card.url + '" />'
              + '<div class="large" style="background-image:url(\'' + card.url + '\')"></div>'
              + '</div>';
    }
    function updateCards(cards, containerId) {
        if (cards === undefined) {
            $(containerId).html('');
            return
        }
        var html = [];
        $.each(cards, function(i, card) {
            html.push(cardCell(card, containerId == '#hand'));
        });
        $(containerId).html(html.join('')).fadeIn();
        $('.card').mousemove(magnifyHandler).mouseout(magnifyHandler);
    }


    // Game board communication
    function sendCommand(cmd, params, callback) {
        if (activeGame === undefined) {
            return;  // error
        }
        return $.getJSON('game/' + activeGame + '/' + cmd + (params ? '?' + params : ''),
                          callback);
    }


    // Handlers to send game commands to server
    $('.joinGame').click(function(e) {
        sendCommand({{ commands.JOIN_GAME }}, 'colour=' + $(this).attr('id'), function(data) {
            refreshGameBoard();
            refreshGameList();
        });
        e.preventDefault();
    });

    function kickPlayer(e) {
        sendCommand({{ commands.KICK_PLAYER }}, 'puid=' + $(this).attr('id'), function(data) {
            refreshGameBoard();
            refreshGameList();
        });
        e.preventDefault();
    };

    $('#startGame').submit(function(e) {
        sendCommand({{ commands.START_GAME }}, null, function(data) {
            refreshGameBoard();
            refreshGameList();
        });
        e.preventDefault();
    });

    function setupActionFormHandler(cmd) {
        return function(e) {
            // Handler for when a card is clicked; sets up the actionForm appropriately
            $('#actionForm').data('cmd', cmd);
            if (cmd == {{ commands.CREATE_CLUE }}) {
                $('#actionOk').val('Create');
                $('#actionClue').show().select();
            } else if (cmd == {{ commands.PLAY_CARD }}) {
                $('#actionOk').val('Play');
                $('#actionClue').hide();
            } else if (cmd == {{ commands.CAST_VOTE }}) {
                $('#actionOk').val('Vote');
                $('#actionClue').hide();
            }
            $('#cardId').val($(this).attr('id'));
            $('#actionBox').css('top', e.pageY).css('left', e.pageX).fadeIn('slow');
        };
    };
    $('#actionForm').submit(function(e) {
        var cmd = $(this).data('cmd');
        if (cmd == {{ commands.CREATE_CLUE }}) {
            if (!$(this).valid()) {
                return e.preventDefault();
            } else {
                post = $(this).serialize()
            }
        } else {
            post = 'cid=' + $('#cardId').val();
        }
        $('#actionBox').hide();
        sendCommand(cmd, post, function(data) {
            refreshGameBoard();
            refreshGameList();
        });
        e.preventDefault();
    });
    $('#actionCancel').click(function(e) {
        $('#actionBox').hide();
        e.preventDefault();
    });
    $('#actionForm').validate();


    // Create a new game
    $('#createTab').click(function() {
        $('#overlay').show();
        $('#create').show();
    });
    function closeCreate(e) {
        $('#overlay').hide();
        $('#create').hide();
        e.preventDefault();
    }
    $('#overlay').click(closeCreate);
    $('#cancelCreate').click(closeCreate);
    $('#createForm').submit(function(e) {
        if (!$(this).valid()) {
            return e.preventDefault();
        }
        $.post($(this).attr('action'), $(this).serialize(), function(response) {
            switchGame(response);
        }, 'json');
        closeCreate(e);
    });
    $('#createForm').validate();


    // Switch current game
    function switchGame(gid) {
        activeGame = gid;
        document.location.hash = 'gid=' + gid;
        refreshGameList();
        refreshGameBoard();
    };


    // Editable username
    $('#username').editable('setusername', {
        name : 'username',
        width : '200',
        tooltip : 'Click to change your name',
        callback : function(value, settings) {
            refreshGameList();
            refreshUserList();
        }
    });


    // Nice card animations
    function animateHand(isUp) {
        $('#handContainer').animate({
            // + 10 to handle padding
            'bottom' : (isUp ? '+' : '-') + '=' + ($('#hand').height() + 10) + 'px'
        });
    };
    function hideHand() {
        animateHand(false);
        $('#showHand').show();
        $('#hideHand').hide();
    };
    $('#hideHand').click(hideHand);
    function showHand() {
        animateHand(true);
        $('#showHand').hide();
        $('#hideHand').show();
    };
    $('#showHand').click(showHand);
    function setHandHidden() {
        if ($('#showHand').is(':hidden')) {
            hideHand();
        }
    };
    function setHandShown() {
        if ($('#hideHand').is(':hidden')) {
            showHand();
        }
    };


    // Static document-wide jQuery handlers
    $(document).tooltip();
    $('button').button();
    $('#actionOk').button();
    $('#createOk').button();
    $('#gameStateContainer').draggable();


    // Chat smiley list
    var smileyList = [];
    $.each(smileys, function(text, image) {
        smileyList.push(text);
    });
    $('#smileyList').html(smilify(smileyList.join(' ')));
    $('#smileyList .smiley').mousedown(function(e) {
        // mousedown handler to prevent focus from being shifted
        var focused = $(':focus');
        if (focused === undefined || (!focused.is('input') && !focused.is('textarea'))) {
            focused = $('#chatInput');
        }
        var chatInput = focused.val();
        if (chatInput == '{{ display.Labels.DEFAULT_TEXT }}') {
            chatInput = '';
        }
        if (chatInput.length > 0 && !chatInput.match(/ $/)) {
            chatInput += ' ';
        }
        chatInput += $(this).attr('ascii');
        focused.val(chatInput).focus()[0].setSelectionRange(chatInput.length, chatInput.length);
        $('#smileyList').fadeOut();
        e.preventDefault();
    });
    $('#toggleSmileyList').html(smilify(':)')).hover(function() {
        $('#smileyList').fadeIn();
    });
    $(document).click(function() {
        $('#smileyList').fadeOut();
    });


    // Switch to game if opening correct URL
    if (activeGame !== undefined) {
        switchGame(activeGame);
    }
});
