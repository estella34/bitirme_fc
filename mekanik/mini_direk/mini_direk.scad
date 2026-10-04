// DepoGöz — masa üstü mini teleskopik direk (tamamı PLA baskı)
//
// Dört iç içe kare boru, üç halat, elle çevrilen vinç. Motor/vinç 1. boruyu x kadar
// kaldırınca halat-makara düzeni 2. boruyu 2x, 3. boruyu 3x kaldırır; boruların
// tepeleri (kamera yerleri) arasındaki mesafe hep eşit kalır.
//
// Kullanım:  openscad -D 'part="tube1"' -o tube1.stl mini_direk.scad
//            part = "assembly" iken x ile açıklık (0..125 mm) gösterilir.
//
// Dışarıdan gerekenler: ~3 m misina veya sağlam ip; makara milleri ve sabitleme
// pimleri için 1,75 mm filament parçaları (aynı makaradan kesilir).

part = "assembly";
x = 60;                       // montaj görünümü: kademe başına açıklık (mm)

// ---------------------------------------------------------------------------
// Ana ölçüler (mm)
W = [70, 52, 34, 16];         // boruların dış genişliği (0 = taban borusu)
T = 2.0;                      // et kalınlığı
L = 220;                      // hareketli boruların boyu
STAGGER = 32;                 // kapalıyken ardışık boru tepeleri arası
L0 = L - STAGGER;             // taban borusu boyu
C = 0.4;                      // pabuç boşluğu: sıkıysa büyüt, sallanıyorsa küçült
FIT = 0.2;                    // yaka eteği / soket geçme boşluğu
PAD_W = 12;                   // pabuç genişliği
MOUTH_H = 10;                 // üst pabuç (yaka) yüksekliği
FOOT_H = 46;                  // alt pabuç (ayak) yüksekliği
RING_H = 4;                   // yaka halkası kalınlığı
SKIRT_T = 1.6;                // yaka eteği kalınlığı
LUG_H = 10;                   // ayaktaki halat kulağı yüksekliği
ROPE_D = 1.6;                 // halat deliği
PIN_D = 1.9;                  // 1,75 mm filament pim deliği
AXLE_D = 1.8;                 // makara mili deliği (kulakta, sıkı)
PLATE_T = 4;                  // taban plakası kalınlığı

// Makara: iki halat şeridi arası = (boşluk + et) * √2
G = (W[0] - 2*T - W[1]) / 2;  // borular arası boşluk (hepsi eşit: 7 mm)
R_G = (G + T) * sqrt(2) / 2;  // makara oluk yarıçapı (halat merkezine)
R_FL = R_G + 1.6;             // flanş yarıçapı
WHEEL_T = 4;
P_CZ = R_FL + 0.8;            // makara merkezinin halka üstünden yüksekliği
EAR_T = 2.2;
EAR_L = 3.0;                  // kulak plakasının köşegen boyunca yarı boyu

$fn = 48;

function gap(k) = (W[k] - 2*T - W[k+1]) / 2;
// Köşe açıları: KD=45, KB=135, GB=225, GD=315 (yerel +x köşegen boyunca dışarı)
NE = 45; NW = 135; SW = 225;
PULLEY_CORNER = [NE, NW, SW];          // yaka k'deki makara köşesi
ANCHOR_CORNER = [NW, SW, -1];          // yaka k'deki halat bağlama köşesi (-1: yok)
FOOT_LUG_CORNER = [-1, NE, NW, SW];    // boru k'nın ayağındaki halat kulağı

// ---------------------------------------------------------------------------
module square_ring(outer, inner, h) {
    linear_extrude(h) difference() { square(outer, center = true); square(inner, center = true); }
}

module teardrop_x(d, len) {           // yatay delik, desteksiz basılsın diye damla kesit
    rotate([0, 90, 0]) linear_extrude(len, center = true)
        union() { circle(d = d); rotate(135) square(d / 2); }   // uç +z'ye bakar
}

// Boru k. Alt ucu z=0.
module tube(k) {
    w = W[k];
    len = k == 0 ? L0 : L;
    difference() {
        union() {
            square_ring(w, w - 2*T, len);
            if (k > 0) {
                p = gap(k - 1) - C;
                for (a = [0:90:270]) rotate(a)          // ayak pabuçları
                    translate([w/2 - 0.01, -PAD_W/2, 0]) cube([p + 0.01, PAD_W, FOOT_H]);
                if (FOOT_LUG_CORNER[k] >= 0)              // halat kulağı
                    rotate(FOOT_LUG_CORNER[k] - 45)
                        difference() {
                            translate([w/2 - T, w/2 - T, 0]) cube([T + gap(k-1) - C, T + gap(k-1) - C, LUG_H]);
                            translate([w/2 + gap(k-1)/2, w/2 + gap(k-1)/2, -1]) cylinder(d = ROPE_D, h = LUG_H + 2);
                        }
            }
        }
        // yaka pim delikleri (x yüzleri) ve taban borusunda soket pimi
        translate([0, 0, len - MOUTH_H/2]) teardrop_x(PIN_D, w + 4);
        if (k == 0) translate([0, 0, 6]) teardrop_x(PIN_D, w + 4);
    }
}

// Yaka k (boru k'nın tepesi). Yerel z=0 borunun tepesi.
module collar(k) {
    w = W[k];
    inner = w - 2*T;
    outer = w + 2*(FIT + SKIRT_T);
    p = gap(k) - C;
    difference() {
        union() {
            // halka: pabuçların üstünü de kapatır
            linear_extrude(RING_H) difference() {
                square(outer, center = true);
                difference() {
                    square(inner, center = true);
                    for (a = [0:90:270]) rotate(a) translate([inner/2 - p, -PAD_W/2]) square([p, PAD_W]);
                }
            }
            // etek (borunun dışında)
            translate([0, 0, -MOUTH_H]) square_ring(outer, w + 2*FIT, MOUTH_H);
            // üst pabuçlar (borunun içinde)
            for (a = [0:90:270]) rotate(a)
                translate([inner/2 - p, -PAD_W/2, -MOUTH_H]) cube([p, PAD_W, MOUTH_H + 0.01]);
            // halat bağlama sütunu (iç köşede)
            if (ANCHOR_CORNER[k] >= 0) rotate(ANCHOR_CORNER[k] - 45)
                difference() {
                    lo = W[k+1]/2 + C;
                    translate([lo, lo, -MOUTH_H]) cube([inner/2 - lo + 0.01, inner/2 - lo + 0.01, MOUTH_H + RING_H]);
                    translate([W[k+1]/2 + G/2, W[k+1]/2 + G/2, -MOUTH_H - 1]) cylinder(d = ROPE_D, h = MOUTH_H + RING_H + 2);
                }
            // makara kulakları + borunun dışında kalan kısmın altına destek ayağı
            if (k < 3) {
                rotate(PULLEY_CORNER[k]) pulley_ears((w/2 - T/2) * sqrt(2));
                difference() {
                    rotate(PULLEY_CORNER[k]) ear_plates((w/2 - T/2) * sqrt(2), -MOUTH_H, MOUTH_H + RING_H);
                    translate([0, 0, -MOUTH_H - 1]) linear_extrude(MOUTH_H + 1) square(w + 2*FIT, center = true);
                }
            }
            // kamera yeri (güney yüzü)
            translate([-5, -outer/2 - 5, -MOUTH_H]) camera_nub();
        }
        // pim delikleri: etek + borunun eti + pabuç (pabucun iç yüzüne 1 mm kala biter)
        for (s = [-1, 1]) translate([s * (outer/2 - (SKIRT_T + FIT + T + p - 1)/2 + 0.5), 0, -MOUTH_H/2])
            teardrop_x(PIN_D, SKIRT_T + FIT + T + p);
    }
}

// Kapak: en içteki borunun tepesi (pabuç ve makara yok).
module cap3() {
    w = W[3];
    outer = w + 2*(FIT + SKIRT_T);
    difference() {
        union() {
            translate([-outer/2, -outer/2, 0]) cube([outer, outer, RING_H]);
            translate([0, 0, -MOUTH_H]) square_ring(outer, w + 2*FIT, MOUTH_H);
            translate([-5, -outer/2 - 5, -MOUTH_H]) camera_nub();
        }
        translate([0, 0, -MOUTH_H/2]) teardrop_x(PIN_D, outer + 2);
    }
}

module camera_nub() {                 // 10x5x8 mm temsilî kamera, önünde "mercek"
    difference() {
        cube([10, 5, 8]);
        translate([5, -0.01, 4]) rotate([-90, 0, 0]) cylinder(d = 4, h = 1.2);
    }
}

// Makara kulakları: yerel +x köşegen, makara merkezi xc'de.
module ear_plates(xc, z0, h) {
    for (s = [-1, 1]) translate([xc - EAR_L, s * (WHEEL_T/2 + 0.4) + (s < 0 ? -EAR_T : 0), z0])
        cube([2*EAR_L, EAR_T, h]);
}
module pulley_ears(xc) {
    difference() {
        ear_plates(xc, RING_H - 0.01, P_CZ + 3);
        translate([xc, 0, RING_H + P_CZ]) rotate([90, 0, 0]) cylinder(d = AXLE_D, h = 20, center = true);
    }
}

// Makara (düz basılır). Ortası 1,75 filament mil için Ø2,0.
module pulley() {
    difference() {
        rotate_extrude($fn = 64) polygon([
            [1.0, 0], [R_FL, 0], [R_FL, 0.8], [R_G, 0.8 + (R_FL - R_G)],
            [R_G, WHEEL_T - 0.8 - (R_FL - R_G)], [R_FL, WHEEL_T - 0.8], [R_FL, WHEEL_T], [1.0, WHEEL_T]
        ]);
        translate([0, 0, -1]) cylinder(d = 2.0, h = WHEEL_T + 2);
    }
}

// ---------------------------------------------------------------------------
// Taban: plaka, taban borusu soketi, kademeli dinlenme kaidesi, yönlendirme makarası,
// vinç yatakları ve kilit pimi yuvası.
D_DRUM = 100;                 // vinç ekseninin köşegen boyunca merkezden uzaklığı
AXIS_H = 48;                  // vinç ekseni yüksekliği (plaka üstünden değil, z=0'dan)
R_DRUM = 10;
SHAFT_D = 8;
LOCK_R = 10;                  // krank göbeğindeki kilit deliklerinin yarıçapı
LOCK_N = 12;

module stand() {
    plate = 200;
    sock_in = W[0] + 2*FIT;
    sock_out = sock_in + 6;
    rope_h = AXIS_H - R_DRUM;                 // yatay halatın yüksekliği
    guide_x = (W[0]/2 + G/2) * sqrt(2) + R_G; // yönlendirme makarası merkezi (köşegen)
    difference() {
        union() {
            translate([-plate/2, -plate/2, 0]) cube([plate, plate, PLATE_T]);
            // soket: köşeleri pahlı (halat KD köşesinden iner)
            translate([0, 0, PLATE_T - 0.01]) intersection() {
                square_ring(sock_out, sock_in, 12);
                rotate(45) cube([sock_out * 1.32, sock_out * 1.32, 40], center = true);
            }
            // dinlenme kaidesi: 2. ve 3. boru kapalıyken bunun üstüne oturur
            translate([0, 0, PLATE_T - 0.01]) linear_extrude(STAGGER + 0.01) square(W[2] + 2*gap(1) - 1, center = true);
            translate([0, 0, PLATE_T - 0.01]) linear_extrude(2*STAGGER + 0.01) square(W[3] + 2*gap(2) - 1, center = true);
            // yönlendirme makarası kulakları (KD köşegeni)
            rotate(NE) for (s = [-1, 1])
                translate([guide_x - 4, s * (WHEEL_T/2 + 0.4) + (s < 0 ? -EAR_T : 0), PLATE_T - 0.01])
                    difference() {
                        cube([8, EAR_T, rope_h + R_G + 4 - PLATE_T]);
                        translate([4, -1, rope_h + R_G - PLATE_T]) rotate([-90, 0, 0]) cylinder(d = AXLE_D, h = EAR_T + 2);
                    }
            // vinç yatakları (üstü açık U), mil köşegene dik
            rotate(NE) translate([D_DRUM, 0, 0]) for (s = [-24, 20])
                translate([-9, s, 0]) difference() {
                    cube([18, 8, AXIS_H + 8]);
                    translate([9, -1, AXIS_H]) rotate([-90, 0, 0]) cylinder(d = SHAFT_D + 0.5, h = 10);
                    translate([9 - (SHAFT_D + 0.5)/2, -1, AXIS_H]) cube([SHAFT_D + 0.5, 10, 20]);
                    // mil tutma pimi (U'nun üstünden geçer)
                    translate([0, 4, AXIS_H + SHAFT_D/2 + 2]) teardrop_x(PIN_D, 40);
                    // kilit pimi deliği (yalnız iç yatakta, kilit diskine bakar)
                    if (s == -24) translate([9, -1, AXIS_H - LOCK_R]) rotate([-90, 0, 0]) cylinder(d = 2.2, h = 10);
                }
        }
        // soket pimi
        translate([0, 0, PLATE_T + 6]) teardrop_x(PIN_D, sock_out + 2);
    }
}

// Vinç: krank (kilit delikli göbek) + mil + tambur. Dik basılır, krank tablaya yatar.
// Krank iç yatağın hemen dışında döner; iç yataktan geçen pim göbekteki bir deliğe
// girince vinç kilitlenir (direk o yükseklikte kalır).
module drum() {
    crank_r = 34;
    union() {
        difference() {
            hull() { cylinder(r = LOCK_R + 4, h = 4); translate([crank_r, 0, 0]) cylinder(d = 10, h = 4); }
            for (i = [0:LOCK_N - 1]) rotate(i * 360 / LOCK_N) translate([LOCK_R, 0, -1]) cylinder(d = 2.4, h = 6);
        }
        translate([crank_r, 0, 0]) cylinder(d = 8, h = 22);          // tutamak
        cylinder(d = SHAFT_D, h = 58);                               // mil
        // tambur: alt flanş 45° koni, gövde, üst flanş 45° koni (desteksiz basılır)
        translate([0, 0, 12.5]) difference() {
            union() {
                cylinder(r1 = SHAFT_D/2, r2 = R_DRUM + 4, h = R_DRUM + 4 - SHAFT_D/2);
                translate([0, 0, 10]) cylinder(r = R_DRUM, h = 16);
                translate([0, 0, 26]) cylinder(r1 = R_DRUM, r2 = R_DRUM + 4, h = 4);
            }
            translate([0, 0, 18]) rotate([90, 0, 0]) cylinder(d = ROPE_D + 0.3, h = 2*R_DRUM + 2, center = true);
        }
    }
}

// ---------------------------------------------------------------------------
// Montaj görünümü (yalnız ön izleme; parça baskısı için kullanılmaz)
function bottom(k) = k == 0 ? PLATE_T : PLATE_T + (k - 1) * STAGGER + k * x;
function top(k) = bottom(k) + (k == 0 ? L0 : L);

module assembly() {
    color("#3a3f47") stand();
    for (k = [0:3]) {
        color(["#d9dde3", "#c3c9d1", "#aeb5bf", "#99a1ad"][k]) translate([0, 0, bottom(k)]) tube(k);
        color("#f2791c") translate([0, 0, top(k)]) if (k < 3) collar(k); else cap3();
        if (k < 3) color("#2f6be4") rotate(PULLEY_CORNER[k])
            translate([(W[k]/2 - T/2) * sqrt(2), 0, top(k) + RING_H + P_CZ]) rotate([90, 0, 0]) translate([0, 0, -WHEEL_T/2]) pulley();
    }
    guide_x = (W[0]/2 + G/2) * sqrt(2) + R_G;
    color("#2f6be4") rotate(NE) translate([guide_x, 0, AXIS_H - R_DRUM + R_G]) rotate([90, 0, 0]) translate([0, 0, -WHEEL_T/2]) pulley();
    color("#f2791c") rotate(NE) translate([D_DRUM, -24 - 4, AXIS_H]) rotate([-90, 0, 0]) drum();
}

// ---------------------------------------------------------------------------
module print_part(name) {
    if (name == "tube0") tube(0);
    else if (name == "tube1") tube(1);
    else if (name == "tube2") tube(2);
    else if (name == "tube3") tube(3);
    else if (name == "collar0") translate([0, 0, MOUTH_H]) collar(0);
    else if (name == "collar1") translate([0, 0, MOUTH_H]) collar(1);
    else if (name == "collar2") translate([0, 0, MOUTH_H]) collar(2);
    else if (name == "cap3") translate([0, 0, MOUTH_H]) cap3();
    else if (name == "pulley") pulley();
    else if (name == "stand") stand();
    else if (name == "drum") drum();
}

if (part == "assembly") assembly(); else print_part(part);
