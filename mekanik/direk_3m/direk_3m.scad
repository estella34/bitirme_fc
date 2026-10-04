// DepoGöz — 3 m eş zamanlı teleskopik direk: basılacak parçalar
//
// Borular hazır alüminyum kare profil (60/45/30/15 mm). Bu dosya yalnız bağlantı
// parçalarını üretir: yakalar, ayak kılıfları, iç tıpalar, değiştirilebilir kayar
// pabuçlar, rulmanlı makaralar, taban yuvası, motor tamburu, kamera plakası.
//
// Kullanım:  openscad -D 'part="collar0"' -o collar0.stl direk_3m.scad
//            part="assembly" → montaj görünümü, x = kademe başına açıklık (mm)

part = "assembly";
x = 300;

// ---------------------------------------------------------------------------
// Borular (alüminyum kare profil)
W = [60, 45, 30, 15];           // dış ölçü (mm)
T = [2, 2, 2, 1.5];             // et kalınlığı
STAGGER = 70;                   // kapalıyken ardışık boru tepeleri arası (kameralar çakışmasın)
L = [900 - STAGGER, 900, 900, 900];   // boru boyları: taban 830, diğerleri 900
X_MAX = 600;                    // normal üst sınır (limit anahtarı); kamera aralığı = STAGGER + x
// Mekanik acil durdurucu: ayak kılıfı yaka parmaklarına dayanınca (x ≈ 750)

G = (W[0] - 2*T[0] - W[1]) / 2; // borular arası boşluk: 5,5 mm (hepsi eşit)

// Kayma
C = 0.4;                        // pabuç ile karşı yüzey arası hedef boşluk
FINGER_T = 2.4;                 // yaka parmağı / ayak kılıfı kalınlığı
PAD_T = G - C - FINGER_T;       // pabuç kalınlığı (2,7); 2,5 ve 2,9 sürümleri de basılır
PAD_W = 16;
PAD_H = 25;
FINGER_W = 22;

// Yaka
COLLAR_H = 35;                  // etek ve parmak derinliği (borunun içine/dışına)
RING_H = 5;
SKIRT_T = 2.5;
FIT = 0.25;                     // yaka eteği - boru boşluğu

// Ayak (hareketli boruların dibi)
SLEEVE_H = 45;
PLUG_H = STAGGER;               // iç tıpa: bir sonraki boru kapalıyken bunun üstüne oturur

// Bağlantı
M3 = 3.4;                       // M3 geçme deliği
INSERT_D = 4.0;                 // M3 ısıyla gömülen somun yuvası
ROPE_D = 2.0;

// Makara: 623ZZ rulman (3x10x4), M3 cıvata mil
R_P = 8;                        // oluk yarıçapı (halat merkezine)
R_FL = 11;
PW = 6;                         // makara genişliği
BRG_D = 10; BRG_W = 4;
P_CZ = R_FL + 1.5;              // makara merkezi, halka üstünden
EAR_T = 3;
EAR_L = 6;

$fn = 48;

NE = 45; NW = 135; SW = 225;
PULLEY_CORNER = [NE, NW, SW];
ANCHOR_CORNER = [NW, SW, -1];
LUG_CORNER = [-1, NE, NW, SW];

function lane(k) = W[k+1]/2 + G/2;              // boşluk k köşe şeridi (x = y)
function pulley_d(k) = lane(k) * sqrt(2) + R_P;  // makara merkezi, köşegen boyunca

// ---------------------------------------------------------------------------
module sq_ring(o, i, h) { linear_extrude(h) difference() { square(o, center = true); square(i, center = true); } }

module teardrop_x(d, len) {
    rotate([0, 90, 0]) linear_extrude(len, center = true)
        union() { circle(d = d); rotate(135) square(d / 2); }
}
module teardrop_y(d, len) { rotate(90) teardrop_x(d, len); }

// Değiştirilebilir kayar pabuç. Sırtı tablada, kayan yüzü üstte basılır (Bambu Studio'da
// "Ütüleme / Ironing: üst yüzeyler" açın → pürüzsüz yüzey). Arkadaki iki kör delikten
// 1,75 mm filament pimle parmağa/kılıfa takılır (isteğe bağlı bir damla yapıştırıcı).
PIN_D = 1.9;
module pad(t = PAD_T) {
    difference() {
        hull() {
            translate([-PAD_W/2, -PAD_H/2 + 1, 0]) cube([PAD_W, PAD_H - 2, t]);
            translate([-PAD_W/2 + 0.6, -PAD_H/2, 0]) cube([PAD_W - 1.2, PAD_H, t - 0.8]);
        }
        for (s = [-1, 1]) translate([0, s * 7, -1]) cylinder(d = PIN_D, h = t - 0.8 + 1);
    }
}

// Parmak/kılıf üstünde pabuç pim delikleri: kalınlık (x) boyunca, dikeyde 14 mm arayla
module pad_holes() { for (s = [-1, 1]) translate([0, 0, s * 7]) rotate([0, 90, 0]) cylinder(d = PIN_D, h = 20, center = true); }

// ---------------------------------------------------------------------------
// Yaka k: boru k'nın tepesine takılır. Yerel z=0 borunun tepesi.
module collar(k) {
    w = W[k]; inner = w - 2*T[k];
    outer = w + 2*(FIT + SKIRT_T);
    difference() {
        union() {
            // halka (parmakların üstünü de kapatır)
            linear_extrude(RING_H) difference() {
                square(outer, center = true);
                difference() {
                    square(inner, center = true);
                    for (a = [0:90:270]) rotate(a) translate([inner/2 - FINGER_T, -FINGER_W/2]) square([FINGER_T, FINGER_W]);
                }
            }
            translate([0, 0, -COLLAR_H]) sq_ring(outer, w + 2*FIT, COLLAR_H);          // etek
            for (a = [0:90:270]) rotate(a)                                              // parmaklar
                translate([inner/2 - FINGER_T, -FINGER_W/2, -COLLAR_H]) cube([FINGER_T, FINGER_W, COLLAR_H + 0.01]);
            // dış etekte vida göbekleri (ısıl somun için), her yüzde bir
            for (a = [0:90:270]) rotate(a) translate([outer/2 - 0.01, -5, -COLLAR_H]) cube([3, 10, 12]);
            // halat bağlama sütunu
            if (ANCHOR_CORNER[k] >= 0) rotate(ANCHOR_CORNER[k] - 45)
                difference() {
                    lo = W[k+1]/2 + C + 0.6;
                    translate([lo, lo, -COLLAR_H]) cube([inner/2 - lo - 0.05, inner/2 - lo - 0.05, COLLAR_H + RING_H]);
                    translate([lane(k), lane(k), -COLLAR_H - 1]) cylinder(d = ROPE_D, h = COLLAR_H + RING_H + 2);
                }
            // makara kulakları (+ borunun dışında kalan kısmın altına destek)
            if (k < 3) {
                rotate(PULLEY_CORNER[k]) pulley_ears(pulley_d(k));
                difference() {
                    rotate(PULLEY_CORNER[k]) ear_plates(pulley_d(k), -COLLAR_H, COLLAR_H + RING_H);
                    translate([0, 0, -COLLAR_H - 1]) linear_extrude(COLLAR_H + 1) square(w + 2*FIT, center = true);
                }
            }
            // kamera plakası (ön yüz, -y)
            translate([0, -outer/2, -COLLAR_H]) camera_plate();
        }
        // pabuç tırnak delikleri (parmaklar, iç yüzden)
        for (a = [0:90:270]) rotate(a) translate([inner/2 - FINGER_T/2, 0, -PAD_H/2 - 2]) pad_holes();
        // M3: içeriden düz/yuvarlak başlı cıvata → parmak + boru eti + etek → etekteki ısıl somun
        for (a = [0:90:270]) rotate(a) translate([0, 0, -COLLAR_H + 4.5]) {
            translate([inner/2 - 5, 0, 0]) rotate([0, 90, 0]) cylinder(d = M3, h = 20);
            translate([outer/2 - 1, 0, 0]) rotate([0, 90, 0]) cylinder(d = INSERT_D, h = 10);
        }
    }
}

// En içteki borunun kapağı (kamera plakalı).
module cap3() {
    w = W[3]; outer = w + 2*(FIT + SKIRT_T);
    difference() {
        union() {
            translate([-outer/2, -outer/2, 0]) cube([outer, outer, RING_H]);
            translate([0, 0, -COLLAR_H]) sq_ring(outer, w + 2*FIT, COLLAR_H);
            translate([0, -outer/2, -COLLAR_H]) camera_plate();
        }
        translate([0, 0, -COLLAR_H + 8]) rotate([0, 90, 0]) cylinder(d = M3, h = outer + 2, center = true);
    }
}

// Kamera plakası: 44x35 mm, iki M3 ısıl somun yuvası (30 mm arayla) + ortada kablo deliği.
module camera_plate() {
    difference() {
        translate([-22, -5, 0]) cube([44, 5.01, COLLAR_H]);
        for (s = [-1, 1]) translate([s * 15, -5.5, COLLAR_H / 2]) rotate([-90, 0, 0]) cylinder(d = INSERT_D, h = 5);
    }
}

module ear_plates(d, z0, h) {
    for (s = [-1, 1]) translate([d - EAR_L, s * (PW/2 + 0.6) + (s < 0 ? -EAR_T : 0), z0]) cube([2*EAR_L, EAR_T, h]);
}
module pulley_ears(d) {
    difference() {
        ear_plates(d, RING_H - 0.01, P_CZ + 5);
        translate([d, 0, RING_H + P_CZ]) rotate([90, 0, 0]) cylinder(d = M3, h = 30, center = true);
    }
}

// Rulmanlı makara (düz basılır, 623ZZ preslenir).
module pulley() {
    difference() {
        rotate_extrude($fn = 72) polygon([
            [BRG_D/2 - 0.5, 0], [R_FL, 0], [R_FL, 0.8], [R_P + 0.4, 0.8 + (R_FL - R_P - 0.4)],
            [R_P - 0.6, PW/2], [R_P + 0.4, PW - 0.8 - (R_FL - R_P - 0.4)], [R_FL, PW - 0.8], [R_FL, PW], [BRG_D/2 - 0.5, PW]
        ]);
        translate([0, 0, (PW - BRG_W)/2]) cylinder(d = BRG_D - 0.1, h = BRG_W + 0.01);   // rulman sıkı geçme
        translate([0, 0, -1]) cylinder(d = BRG_D - 1.5, h = PW + 2);
    }
}

// ---------------------------------------------------------------------------
// Ayak kılıfı: boru k'nın (k≥1) dibini dıştan sarar; dış yüzlerinde pabuçlar, köşede halat kulağı.
module sleeve(k) {
    w = W[k];
    difference() {
        union() {
            // köşeleri pahlı bant (köşe şeritlerine yer kalsın)
            intersection() {
                sq_ring(w + 2*FINGER_T, w + 2*FIT, SLEEVE_H);
                rotate(45) cube([(w/2 + FINGER_T) * sqrt(2) * 2 - 3, (w/2 + FINGER_T) * sqrt(2) * 2 - 3, 3*SLEEVE_H], center = true);
            }
            if (LUG_CORNER[k] >= 0) rotate(LUG_CORNER[k] - 45)
                difference() {
                    translate([w/2 + FIT, w/2 + FIT, 0]) cube([G - C - FIT, G - C - FIT, 12]);
                    translate([w/2 + G/2, w/2 + G/2, -1]) cylinder(d = ROPE_D, h = 14);
                }
        }
        for (a = [0:90:270]) rotate(a) {
            translate([w/2 + FINGER_T/2, 0, SLEEVE_H - PAD_H/2 - 3]) pad_holes();   // pabuçlar üst kısımda
            translate([w/2 - 1, 0, 8]) rotate([0, 90, 0]) cylinder(d = M3, h = 10);                   // M3, alt kısımda
        }
    }
}

// İç tıpa: boru k'nın dibini içten doldurur; ayak cıvataları buna (ısıl somuna) bağlanır.
// k=1,2 için üstü bir sonraki borunun kapalıyken oturduğu yerdir (yüksekliği STAGGER).
module plug(k) {
    i = W[k] - 2*T[k] - 2*FIT;
    h = k < 3 ? PLUG_H : 20;
    difference() {
        translate([-i/2, -i/2, 0]) cube([i, i, h]);
        for (a = [0:90:270]) rotate(a) translate([i/2 - 6, 0, 8]) rotate([0, 90, 0]) cylinder(d = INSERT_D, h = 7);
    }
}

// ---------------------------------------------------------------------------
// Taban yuvası: 60'lık boruyu tutar, robot plakasına 4×M5 ile bağlanır; içinde 1. borunun
// oturduğu taban; köşede motor halatını yatay çeviren makaranın kulakları.
FLANGE = 130; FLANGE_T = 6; SOCKET_H = 50;   // borular flanşın üstüne oturur
GUIDE_D = pulley_d(0) + 2*R_P;      // yönlendirme makarası merkezi (köşegen)
GUIDE_Z = 30;

module base() {
    so = W[0] + 2*FIT + 8;
    difference() {
        union() {
            translate([-FLANGE/2, -FLANGE/2, 0]) cube([FLANGE, FLANGE, FLANGE_T]);
            intersection() {
                translate([0, 0, 0]) sq_ring(so, W[0] + 2*FIT, SOCKET_H);
                rotate(45) cube([so * 1.25, so * 1.25, 3*SOCKET_H], center = true);
            }
            rotate(NE) for (s = [-1, 1]) translate([GUIDE_D - EAR_L, s * (PW/2 + 0.6) + (s < 0 ? -EAR_T : 0), 0])
                difference() {
                    cube([2*EAR_L, EAR_T, GUIDE_Z + 7]);
                    translate([EAR_L, -1, GUIDE_Z]) rotate([-90, 0, 0]) cylinder(d = M3, h = EAR_T + 2);
                }
        }
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * 55, sy * 55, -1]) cylinder(d = 5.5, h = FLANGE_T + 2);
        translate([0, 0, 25]) rotate([0, 90, 0]) cylinder(d = 4.4, h = so + 2, center = true);   // M4 boydan boya
        translate([0, 0, -1]) cylinder(d = 20, h = FLANGE_T + 2);                                 // toz deliği
    }
}

// Motor tamburu: JGY-370 sınıfı 6 mm D milli motor; M3 ısıl somunla sıkılır.
module drum() {
    difference() {
        union() {
            cylinder(r = 15, h = 2);
            translate([0, 0, 2]) cylinder(r = 10, h = 18);
            translate([0, 0, 20]) cylinder(r1 = 10, r2 = 14, h = 4);
        }
        translate([0, 0, -1]) intersection() { cylinder(d = 6.15, h = 30); translate([-3.1, -3.1, 0]) cube([6.2, 5.6, 30]); }
        translate([0, 0, 8]) rotate([-90, 0, 0]) cylinder(d = INSERT_D, h = 12);   // vida milin düz yüzüne basar
        translate([0, 0, 14]) rotate([0, 90, 0]) cylinder(d = ROPE_D, h = 30, center = true);
    }
}

// Delme şablonu yok: yaka eteği ve ayak kılıfındaki delikler şablon görevi görür.

// ---------------------------------------------------------------------------
// Montaj görünümü
function bottom(k) = FLANGE_T + (k == 0 ? 0 : (k - 1) * STAGGER + k * x);
function top(k) = bottom(k) + L[k];

module tube_al(k) color("#c8ccd2") sq_ring(W[k], W[k] - 2*T[k], L[k]);

module assembly() {
    color("#3a3f47") base();
    for (k = [0:3]) {
        translate([0, 0, bottom(k)]) tube_al(k);
        color("#f2791c") translate([0, 0, top(k)]) if (k < 3) collar(k); else cap3();
        if (k > 0) {
            color("#2f6be4") translate([0, 0, bottom(k)]) sleeve(k);
            color("#55606e") translate([0, 0, bottom(k)]) plug(k);
        }
        if (k < 3) color("#1d2530") rotate(PULLEY_CORNER[k])
            translate([pulley_d(k), 0, top(k) + RING_H + P_CZ]) rotate([90, 0, 0]) translate([0, 0, -PW/2]) pulley();
    }
    color("#1d2530") rotate(NE) translate([GUIDE_D, 0, GUIDE_Z]) rotate([90, 0, 0]) translate([0, 0, -PW/2]) pulley();
}

module print_part(name) {
    if (name == "collar0") translate([0, 0, COLLAR_H]) collar(0);
    else if (name == "collar1") translate([0, 0, COLLAR_H]) collar(1);
    else if (name == "collar2") translate([0, 0, COLLAR_H]) collar(2);
    else if (name == "cap3") translate([0, 0, COLLAR_H]) cap3();
    else if (name == "sleeve1") sleeve(1);
    else if (name == "sleeve2") sleeve(2);
    else if (name == "sleeve3") sleeve(3);
    else if (name == "plug1") plug(1);
    else if (name == "plug2") plug(2);
    else if (name == "plug3") plug(3);
    else if (name == "pad_2.5") pad(2.5);   // sırt tablada, kayan yüz üstte (ütüleme)
    else if (name == "pad_2.7") pad(2.7);   // sırt tablada, kayan yüz üstte (ütüleme)
    else if (name == "pad_2.9") pad(2.9);   // sırt tablada, kayan yüz üstte (ütüleme)
    else if (name == "pulley") pulley();
    else if (name == "base") base();
    else if (name == "drum") drum();
}

if (part == "assembly") assembly(); else print_part(part);
