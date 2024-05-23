pureWhite = ['#ffffff',[255, 255, 255],]
pureBlack = ['#000000',[0, 0, 0],]

def get_color(__name):
    t = colors[__name]
    return t['colors'][t['color2']][0]

def dimmer(hexstring):

    r = float(int(hexstring[1:3],16)) * .8
    g = float(int(hexstring[3:5],16)) * .8
    b = float(int(hexstring[5:7],16)) * .8

    rgbZ = [0,0,0]
    rgbZ[0] = int(r)
    rgbZ[1] = int(g)
    rgbZ[2] = int(b) 

    rgb_s = '#'+ hex(rgbZ[0])[2:].rjust(2,'0') + hex(rgbZ[1])[2:].rjust(2,'0') + hex(rgbZ[2])[2:].ljust(2,'0')
    return rgb_s

colors = {
    
    'ATL': {
        'color1': 'red',
        'color2': 'white',
        'colors': {
            'red': [ '#c8102e',[200, 16, 46]],
            'green': [ '#c4d600',[196, 214, 0]],
            'white': pureWhite,
            'gray': [ '#25282a',[37, 40, 42]],
            },
    },

    'BKN': {
        'color1': 'black',
        'color2': 'white',
        'colors': {
            'black': [ '#010101',[1, 1, 1]],
            'white': pureWhite,
        },
    },

    'BOS': {
        'color1': 'green',
        'color2': 'white',
        'colors': {
            'green': [ '#007a33',[0, 122, 51]],
            'black': pureBlack,
            'white': pureWhite,
            'gold': [ '#ffd700',[255, 215, 0]],
            'silver': [ '#c0c0c0',[192, 192, 192]],
        },
    },

    'CHA': {\
        'color1': 'purple',
        'color2': 'teal',
        'colors': {
            'gold': [ '#201747',[32, 23, 71]],
            'teal': [ '#00778b',[0, 119, 139]],
            'white': pureWhite,
            'gray': [ '#888b8d',[136, 139, 141]],
        },
    },
    
    'CHI': {
        'color1': 'red',
        'color2': 'red',
        'colors': {
            'red': [ '#ba0c2f',[186, 12, 47]],
            'black': pureBlack,
            'white': pureWhite,
        },
    },

    'CLE': {
        'color1': 'wine',
        'color2': 'gold',
        'colors': {
            'wine': [ '#6f263d',[111, 38, 61]],
            'white': pureWhite,
            'navy': [ '#041e42',[4, 30, 66]],
            'gold': [ '#ffb81c',[255, 184, 28]],
        },
    },

    'DAL': {
        'color1': 'blue',
        'color2': 'silver',
        'colors': {
            'blue': [ '#0050b5',[0, 80, 181]],
            'silver': [ '#8d9093',[141, 144, 147]],
            'navy': [ '#0c2340',[12, 35, 64]],
            'black': pureBlack,
            'white': pureWhite,
        },
    },

    'DEN': {
        'color1': 'blue',
        'color2': 'gold',
        'colors': {
            'blue': [ '#418fde',[65, 143, 222]],
            'gold': [ '#ffc72c',[255, 199, 44]],
            'navy': [ '#0c2340',[12, 35, 64]],
            'white': pureWhite,
        },
    },
 
    'DET': {
        'color1': 'blue',
        'color2': 'red',
        'colors': {
            'blue': [ '#003da5',[0, 61, 165]],
            'red': [ '#d50032',[213, 0, 50]],
            'navy': [ '#041e42',[4, 30, 66]],
            'white': pureWhite,
        },
    },

    'GSW': {
        'color1': 'gold',
        'color2': 'blue',
        'colors': {
            'gold': ['#ffc72d', [255, 199, 44]],
            'blue': [ '#003da5', [0, 61, 165]],
            },
        },
 
    'HOU': {
        'color1': 'red',
        'color2': 'silver',
        'colors': {
        'red': [ '#ba0c2f',[186, 12, 47]],
            'silver': [ '#8d9093',[141, 144, 147]],
            'yellow': [ '#fdb927',[253, 185, 39]],
            'white': pureWhite,
            'black': pureBlack,
        },
    },

    'IND': {
        'color1': 'blue',
        'color2': 'gold',
        'colors': {
            'blue': [ '#041e42',[4, 30, 66]],
            'gold': [ '#ffb81c',[255, 184, 28]],
            'silver': [ '#b1b3b3',[177, 179, 179]],
            'white': pureWhite,
        },
    },

    'LAC': {
        'color1': 'red',
        'color2': 'blue',
        'colors': {
            'red': [ '#d50032',[213, 0, 50]],
            'blue': [ '#003da5',[0, 61, 165]],
            'silver': [ '#b1b3b3',[177, 179, 179]],
            'white': pureWhite,
            },
        },
 
    'LAL': {
        'color1': 'purple',
        'color2': 'gold',
        'colors': {
            'purple': [ '#702f8a',[112, 47, 138]],
            'gold': [ '#ffc72c',[255, 199, 44]],
            'white': pureWhite,
        },
    },

    'MEM': {
        'color1': 'midnightBlue',
        'color2': 'bealeStreetBlue',
        'colors': {
            'midnightBlue': ['#23375b',[35, 55, 91]],
            'bealeStreetBlue': [ '#6189b9',[97, 137, 185]],
            'smokeBlue': [ '#bbd1e4',[187, 209, 228]],
            'gold': [ '#ffd432',[255, 215, 50]],
        },
    },

    'MIA': {
        'color1': 'red',
        'color2': 'red',
        'colors': {
            'red': [ '#862633', [134, 38, 51]],
            'yellow': [ '#ffa300',[255, 163, 0]],
            'white': pureWhite,
            'black': pureBlack,
        },
    },
    
    'MIL': {
        'color1': 'green',
        'color2': 'cream',
        'colors': { 
        'green': [ '#2c5234', [44, 82, 52]],
            'cream': [ '#ddcba4',[221, 203, 164]],
            'blue': [ '#0057b8', [0, 87, 184]],
            'white': pureWhite,
            'black': pureBlack,
        },
    },

    'MIN': {
        'color1': 'blue',
        'color2': 'green',
        'colors': {
            'blue': [ '#002b5c',[0, 42, 92]],
            'gray': [ '#c6cfd4',[198, 208, 215]],
            'green': [ '#7ac143',[122, 192, 67]],
            'white': pureWhite,
        },
    },

    'NOP': {
        'color1': 'blue',
        'color2': 'red',
        'colors': {
            'blue': [ '#002b5c',[0, 43, 92]],
            'gold': [ '#b4975a',[180, 151, 90]],
            'red': [ '#e31937',[227, 25, 55]],
            'white': pureWhite,
        },
    },

    'NYK': {
        'color1': 'blue',
        'color2': 'orange',
        'colors': {
            'blue': [ '#003da5',[0, 61, 165]],
            'orange': [ '#ff671f',[255, 103, 31]],
            'silver': [ '#b1b3b3',[177, 179, 179]],
            'white': pureWhite,
        },
    },

    'OKC': {
        'color1': 'blue',
        'color2': 'orange',
        'colors': {
            'blue':   ['#007dc3',[0, 125, 195]],
            'orange': ['#f05133',[240, 81, 51]],
            'yellow': ['#fdbb30',[253, 187, 48]],
            'darkBlue': ['#002d62',[0, 45, 98]],
        },
    },

    'ORL': {
        'color1': 'blue',
        'color2': 'silver',
        'colors': {
            'blue': [ '#007dc5',[0, 125, 197]],
            'silver': [ '#c4ced3',[196, 206, 211]],
            'white': pureWhite,
            'black': pureBlack,
        },
    },

    'PHI': {
        'color1': 'blue',
        'color2': 'red',
        'colors': {
            'blue': [ '#006bb6',[0, 102, 182]],
            'red': [ '#ed174c',[237, 23, 76]],
            'white': pureWhite,
        },
    },

    'PHX': {
        'color1': 'orange',
        'color2': 'purple',
        'colors': {
            'orange': [ '#e56020',[229, 96, 32]],
            'gold': [ '#1d1160',[29, 17, 96]],
            'gray': [ '#63717a',[99, 113, 122]],
            'purple': ['#1d1160',[29, 17, 96]],
            'white': pureWhite,
            'black': pureBlack,
            },
    },

    'POR': {
        'color1': 'red',
        'color2': 'silver',
        'colors': {
            'red': [ '#f0163a',[240, 22, 58]],
            'silver': [ '#b6bfbf',[182, 191, 191]],
            'white': pureWhite,
            'black': pureBlack,
        },
    },

    'SAC': {
        'color1': 'purple',
        'color2': 'silver',
        'colors': {
            'gold': [ '#724c9f',[114, 76, 159]],
            'silver': [ '#8e9090',[142, 144, 144]],
            'white': pureWhite,
            'black': pureBlack,
        },
    },

    'SAS': {
        'color1': 'silver',
        'color2': 'silver',
        'colors': {
            'silver': [ '#b6bfbf',[182, 191, 191]],
            'white': pureWhite,
            'black': pureBlack,
        },
    },

    'TOR': {
        'color1': 'red',
        'color2': 'silver',
        'colors': {
            'red': [ '#ce1141',[206, 17, 65]],
            'silver': [ '#c4ced3',[196, 206, 211]],
            'white': pureWhite,
            'black': pureBlack,
        },
    },

    'UTA': {
        'color1': 'navy',
        'color2': 'yellow',
        'colors': {
            'navy': [ '#002b5c',[0, 43, 92]],
            'yellow': [ '#f9a01b',[249, 160, 27]],
            'green': [ '#00471b',[0, 71, 27]],
            'gray': [ '#bec0c2', [190, 192, 194]],
        },
    },

    'WAS': {
        'color1': 'navy',
        'color2': 'red',
        'colors': {
            'navy': [ '#0c2340', [12, 35, 64]],
            'red': [ '#c8102e',[200, 16, 46]],
            'silver': [ '#8d9093',[141, 144, 147]],
            'white': pureWhite, 
        },
    },
}
