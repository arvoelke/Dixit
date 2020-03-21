// Dictionary of unescaped ASCII code to smiley image filename
var smileys = {
    ':)' : 'Smile',
    ':d' : 'Big-Grin',
    '(lol)' : 'Laughing',
    ':p' : 'Tongue',
    ';)' : 'Winking',
    ':(' : 'Sad',
    ';_;' : 'Crying',
    ':\'(' : 'Crying2',
    ':@' : 'Angry',
    '(shh)' : 'Don\'t-tell-Anyone',
    ':|' : 'Straight-Face',
    ':x' : 'Not-Talking',
    '(wtf)' : 'Scared',
    ':s' : 'Confused',
    '(hmm)' : 'Thinking',
    '(!)' : 'Lightbulb',
    '(phew)' : 'Whew',
    'o:)' : 'Sacred',
    '(h)' : 'Smug',
    '8)' : 'Nerd',
    '(dizzy)' : 'Dizzy',
    '(silly)' : 'Silly',
    '<:)' : 'Party',
    '(clown)' : 'Clown',
    '(balloon)' : 'Balloon',
    '(cake)' : 'Cake',
    '<3' : 'Heart',
    '(flower)' : 'Flower',
    '(k)' : 'Kiss',
    '^3^' : 'Love',
    '(gift)' : 'Gift',
    '</3' : 'Broken-Heart',
    '(meow)' : 'Cat',
    '(woof)' : 'Dog',
    '(gee)' : 'Bunny',
    '(oink)' : 'Pig',
    '(ghost)' : 'Ghost',
    '(zombie)' : 'Zombie',
    '(cold)' : 'Cold',
    '(dead)' : 'Dead',
    '(devil)' : 'Devil',
    '(ninja)' : 'Ninja',
    '(drink)' : 'Drinks',
    '(girl)' : 'Girl',
    '(hug)' : 'Hug',
    'o*' : 'Bomb',
    '(clock)' : 'Clock',
    '(mail)' : 'Mail',
    '(music)' : 'Music',
    '(phone)' : 'on-the-Phone',
    '(wave)' : 'Wave',
    '(rainbow)' : 'Rainbow',
    '(rain)' : 'Raining',
    '(drool)' : 'Drooling',
    '(sick)' : 'Sick',
    '(smoke)' : 'Smoking',
    '(sweat)' : 'Sweating',
    '(poo)' : 'Poo',
    '(puke)' : 'Vomit',
    '(*)' : 'Stars',
    '(sun)' : 'Sun',
    '(night)' : 'Night',
    '(yawn)' : 'Yawn',
    '(zzz)' : 'Sleeping',
    '(y)' : 'Cool',
    '(hi5)' : 'Goodbye',
    '(gtfo)' : 'Middle-Finger',
    '(loser)' : 'Loser',
    '(winner)' : 'Win',
};


// Escape a string for use within a regex pattern
function escapeRegExp(str) {
  return str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
}


// Make text safe to add to an HTML element
function textToHtml(text) {
    return $('<div/>').text(text).html();
};


// Replace occurrences of smileys with their images
var escapedSmileys = {};  // smileys with the keys passed through textToHtml
var texts = [];
$.each(smileys, function(text, image) {
    var html = textToHtml(text);
    escapedSmileys[html] = image;
    texts.push(escapeRegExp(html));
});
var smileyRegex = new RegExp(texts.join('|'), 'gmi');  // matches escaped smileys
function smilifyText(text, path) {
    // Convert the text to html and replace in all the smiley images
    return textToHtml(text).replace(smileyRegex, function(match) {
        return '<img class="smiley" src="' + path + '/' + escapedSmileys[match.toLowerCase()]
              + '.png" title="' + match + '" ascii="' + match + '" />';
    });
};
