/*
 * Sef Projesi - Esik karsilastirmasinin sinir-deger testi (C tarafi)
 * ==================================================================
 *
 * NEDEN: Faz 1 Python'da calisiyor ve Python tamsayilari keyfi buyuklukte,
 * yani 127 + 1 her zaman 128'dir. Bu dosyadaki hata Python'da OLUSMAZ.
 * Ama Faz 2/3'te gercek zamanli ajan C'ye tasinirsa, skor dar bir tipe
 * yazildigi anda sessizce sarar ve esik kontrolu yanlis karar verir:
 *
 *     signed char skor = 128;   ->  bellekte 10000000  ->  -128 olarak okunur
 *     if (skor > 100)           ->  (-128 > 100) YANLIS  ->  kapi acilir
 *
 * Supheli dosya "temiz" diye gecer. Bu dosya o hatayi bir regresyon testi
 * olarak sabitler: hatali surum tabloda COKMELI, dogru surum GECMELI.
 *
 * Kullanim:
 *   Paylasimli kutuphane (Python kosucusu icin):
 *     Linux:           gcc -shared -fPIC -O1 -o esik_sinir.so esik_sinir.c
 *     Windows (MinGW): gcc -shared -O1 -o esik_sinir.dll esik_sinir.c
 *   Tek basina calistirilabilir test:
 *     gcc -DSEF_TEST_MAIN -O1 -o esik_sinir esik_sinir.c && ./esik_sinir
 *   Derleyici hatayi yakaliyor mu (asil ders) - projenin C varsayilani:
 *     gcc -fsyntax-only -Wall -Wextra -Wconversion -Wsign-conversion esik_sinir.c
 *   Beklenen: TEK uyari, esik_asti_hatali icindeki daralma satirinda.
 *   Bu dosya hatayi BILEREK icerdigi icin -Werror'siz derlenir; ajan kodunda
 *   ayni bayraklar -Werror ile kullanilir (CLAUDE.md, Kritik Kural 7).
 */

#include <stdbool.h>
#include <stdint.h>

/* Esik ve gecerli skor araligi. Gercek modelde skor 0-100 olasilik
 * yuzdesi olacak; aralik bilerek 255'e kadar genis tutuldu ki sinir
 * degerler (127/128/255) testte gercekten denenebilsin. */
#define ESIK      100
#define SKOR_MIN    0
#define SKOR_MAX  255

/*
 * HATALI SURUM - Faz 2'de yazilmasi muhtemel hali.
 * Skor genis bir tipte hesaplanip dar bir tipe yaziliyor. Cast YOK:
 * daralma ortuluk (implicit), cunku gercek hayatta da kimse bilerek
 * cast yazmaz - "char yeter" diye dusunup gecer.
 * 128 ve 255 burada negatife sarar ve kontrolu atlatir.
 */
bool esik_asti_hatali(int ham_skor)
{
    signed char skor = ham_skor;   /* <-- sessiz daralma: hata tam burada */
    return skor > ESIK;
}

/*
 * DOGRU SURUM.
 * Iki savunma birlikte:
 *   1) Genis tip (int32_t) - sarma olmuyor.
 *   2) Aralik dogrulamasi - beklenmeyen deger "supheli" sayilip kapi
 *      KAPANIYOR (fail-closed). Bir guvenlik kapisinda hesap bozulduysa
 *      dogru varsayilan, dosyayi iceri almak degil isaretlemektir.
 */
bool esik_asti_dogru(int32_t ham_skor)
{
    if (ham_skor < SKOR_MIN || ham_skor > SKOR_MAX) {
        return true;               /* aralik disi = supheli */
    }
    return ham_skor > ESIK;
}

#ifdef SEF_TEST_MAIN
#include <stdio.h>

struct sinir_durumu {
    int  skor;
    bool beklenen;                 /* esik_asti_dogru'nun dondurmesi gereken */
    const char *not_;
};

/* Sinir tablosu. 128 ve 255 satirlari hatali surumu dusuren satirlar. */
static const struct sinir_durumu TABLO[] = {
    {   0, false, "taban"                                   },
    { 100, false, "esige esit - asmiyor"                     },
    { 101, true,  "esigin bir ustu"                          },
    { 127, true,  "signed char tavani"                       },
    { 128, true,  "TASMA SINIRI - hatali surumde -128 olur"  },
    { 255, true,  "unsigned tavani - hatali surumde -1 olur" },
    {  -1, true,  "aralik disi - fail-closed, supheli sayilir"},
};
#define TABLO_N (int)(sizeof(TABLO) / sizeof(TABLO[0]))

int main(void)
{
    int dogru_hata = 0, hatali_hata = 0;

    printf("skor | beklenen | dogru   | hatali  | not\n");
    printf("-----+----------+---------+---------+--------------------------\n");

    for (int i = 0; i < TABLO_N; i++) {
        bool d = esik_asti_dogru(TABLO[i].skor);
        bool h = esik_asti_hatali(TABLO[i].skor);

        if (d != TABLO[i].beklenen) dogru_hata++;
        if (h != TABLO[i].beklenen) hatali_hata++;

        printf("%4d | %-8s | %-7s | %-7s | %s%s\n",
               TABLO[i].skor,
               TABLO[i].beklenen ? "supheli" : "temiz",
               d ? "supheli" : "temiz",
               h ? "supheli" : "temiz",
               (h != TABLO[i].beklenen) ? "[KACIRDI] " : "",
               TABLO[i].not_);
    }

    printf("\nDOGRU surum : %d/%d gecti\n", TABLO_N - dogru_hata, TABLO_N);
    printf("HATALI surum: %d/%d gecti (bu satirlarin kacmasi BEKLENIYOR)\n",
           TABLO_N - hatali_hata, TABLO_N);

    /* Test yalnizca dogru surum kusursuzsa ve hatali surum gercekten
     * kaciriyorsa basarili. Hatali surum de gecerse tablo artik tasmayi
     * olcmuyor demektir - testin kendisi bozulmustur. */
    if (dogru_hata != 0) {
        printf("\nSONUC: BASARISIZ - dogru surum sinirlarda hata yapti.\n");
        return 1;
    }
    if (hatali_hata == 0) {
        printf("\nSONUC: BASARISIZ - hatali surum de gecti, tablo tasmayi "
               "artik yakalamiyor.\n");
        return 1;
    }
    printf("\nSONUC: BASARILI - dogru surum saglam, tasma yakalandi.\n");
    return 0;
}
#endif /* SEF_TEST_MAIN */
