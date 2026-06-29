#!/usr/bin/env bash
# Configura a interface USB para a rede do EV3 (10.42.0.x).

EV3_IP="10.42.0.3"
HOST_IP="10.42.0.1"

_find_usb_iface() {
    for iface in usb0 usb1; do
        if ip link show "$iface" &>/dev/null; then
            echo "$iface"
            return
        fi
    done
    ip -o link show | awk -F': ' '{print $2}' | awk '{print $1}' | grep -E '^(usb|enx)' | head -1
}

setup_usb_network() {
    local iface
    iface=$(_find_usb_iface)

    if [ -z "$iface" ]; then
        echo "Nenhuma interface USB encontrada. Verifique o cabo USB."
        exit 1
    fi

    echo "Interface USB: $iface"

    if ip addr show "$iface" 2>/dev/null | grep -q "$HOST_IP"; then
        echo "$iface já configurada com $HOST_IP"
        return 0
    fi

    if ping -c 1 -W 1 "$EV3_IP" &>/dev/null; then
        echo "EV3 já acessível em $EV3_IP"
        return 0
    fi

    echo "Configurando $iface com $HOST_IP ..."
    sudo ip addr flush dev "$iface"
    sudo ip addr add "$HOST_IP/24" dev "$iface"
    sudo ip link set "$iface" up

    echo "Aguardando EV3 ($EV3_IP)..."
    local attempts=0
    while ! ping -c 1 -W 1 "$EV3_IP" &>/dev/null; do
        attempts=$((attempts + 1))
        if [ "$attempts" -ge 10 ]; then
            echo "Não foi possível alcançar o EV3 em $EV3_IP após 10 tentativas."
            echo "Verifique se o EV3 está ligado e o cabo USB conectado."
            exit 1
        fi
        sleep 1
    done

    echo "EV3 acessivel em $EV3_IP via $iface"
}
