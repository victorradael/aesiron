import streamlit as st
from core.equipment_manager import (
    load_equipment_sets,
    add_equipment_set,
    update_equipment_set,
    delete_equipment_set,
    clone_equipment_set,
    update_equipment_acquisition,
)

EQUIPMENT_TYPES = {
    "capacete": "🪖 Capacete",
    "peitoral": "👕 Peitoral",
    "calças": "👖 Calças",
    "anel_1": "💍 Anel 1",
    "anel_2": "💍 Anel 2",
    "colar": "📿 Colar",
    "mochila": "🎒 Mochila",
    "mao_secundaria": "🛡️ Mão Secundária",
}


def render_registration_screen():
    st.header("📋 Novo Conjunto")
    st.markdown(
        "Crie um novo conjunto, selecione as partes e defina nomes personalizados para ter controle total do seu inventário."
    )

    with st.container(border=True):
        with st.form("registration_form"):
            set_name = st.text_input(
                "NOME DO CONJUNTO", placeholder="Ex: Armadura de Batalha Sagrada"
            )

            st.divider()
            st.subheader("🧩 Peças do Conjunto")
            st.caption(
                "Selecione quais itens formam este conjunto e o nome específico de cada um deles (opcional)."
            )

            equipment_flags = {}
            custom_names = {}

            for key, base_label in EQUIPMENT_TYPES.items():
                cols = st.columns([1, 2], vertical_alignment="center")
                with cols[0]:
                    has_in_set = st.checkbox(
                        base_label, value=True, key=f"new_{key}_check"
                    )
                    equipment_flags[key] = has_in_set
                with cols[1]:
                    custom_name = st.text_input(
                        "Nome Específico",
                        key=f"new_{key}_name",
                        disabled=not has_in_set,
                        label_visibility="collapsed",
                        placeholder=f"Nome do {base_label.split(' ')[1]}...",
                    )
                    custom_names[key] = custom_name.strip()

            st.divider()
            submitted = st.form_submit_button(
                "Criar Conjunto", type="primary", use_container_width=True
            )

            if submitted:
                if not set_name.strip():
                    st.error("⚠️ Por favor, insira um nome para o conjunto.")
                else:
                    add_equipment_set(set_name, equipment_flags, custom_names)
                    st.success(f"✅ Conjunto '{set_name}' salvo com sucesso!")


def render_edit_screen(set_data):
    st.header(f"✏️ Editar: {set_data['name']}")

    with st.container(border=True):
        with st.form(f"edit_form_{set_data['id']}"):
            new_set_name = st.text_input("NOME DO CONJUNTO", value=set_data["name"])

            st.divider()
            st.subheader("🧩 Peças do Conjunto")

            equipment_flags = {}
            custom_names = {}

            for key, base_label in EQUIPMENT_TYPES.items():
                item_data = set_data["equipment"].get(key, {})
                current_has_in_set = item_data.get("has_in_set", False)
                current_custom_name = item_data.get("custom_name", "")

                cols = st.columns([1, 2], vertical_alignment="center")
                with cols[0]:
                    has_in_set = st.checkbox(
                        base_label,
                        value=current_has_in_set,
                        key=f"edit_{set_data['id']}_{key}_check",
                    )
                    equipment_flags[key] = has_in_set
                with cols[1]:
                    custom_name = st.text_input(
                        "Nome Específico",
                        value=current_custom_name,
                        key=f"edit_{set_data['id']}_{key}_name",
                        disabled=not has_in_set,
                        label_visibility="collapsed",
                    )
                    custom_names[key] = custom_name.strip()

            st.divider()
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                submitted = st.form_submit_button(
                    "Salvar Alterações", type="primary", use_container_width=True
                )
            with col2:
                canceled = st.form_submit_button("Cancelar", use_container_width=True)
            with col3:
                deleted = st.form_submit_button("🗑️ Excluir", use_container_width=True)

            if submitted:
                if not new_set_name.strip():
                    st.error("⚠️ O nome não pode ser vazio.")
                else:
                    update_equipment_set(
                        set_data["id"], new_set_name, equipment_flags, custom_names
                    )
                    st.session_state.edit_mode_id = None
                    st.success("✅ Conjunto atualizado!")
                    st.rerun()

            if canceled:
                st.session_state.edit_mode_id = None
                st.rerun()

            if deleted:
                delete_equipment_set(set_data["id"])
                st.session_state.edit_mode_id = None
                st.success("🗑️ Conjunto removido!")
                st.rerun()


def render_checklist_screen():
    if "edit_mode_id" not in st.session_state:
        st.session_state.edit_mode_id = None

    sets = load_equipment_sets()

    if st.session_state.edit_mode_id:
        target_set = next(
            (s for s in sets if s["id"] == st.session_state.edit_mode_id), None
        )
        if target_set:
            render_edit_screen(target_set)
            return
        else:
            st.session_state.edit_mode_id = None

    st.header("🎯 Tracking de Equipamentos")
    st.markdown("Acompanhe o seu progresso na aquisição das peças de cada conjunto.")

    if not sets:
        st.warning("Nenhum conjunto encontrado.", icon="👻")
        st.info(
            "Utilize a navegação lateral para ir à aba 'Cadastro de Conjunto' e criar o seu primeiro set de equipamentos."
        )
        return

    for s in sets:
        # Calculate progress
        items_in_set = {
            k: v for k, v in s["equipment"].items() if v.get("has_in_set", False)
        }
        total_items = len(items_in_set)
        acquired_items = sum(
            1 for data in items_in_set.values() if data.get("acquired", False)
        )

        progress_val = (acquired_items / total_items) if total_items > 0 else 0
        is_complete = total_items > 0 and acquired_items == total_items

        expander_title = f"{'🏆 ' if is_complete else '🛡️ '}{s['name']} - {acquired_items}/{total_items}"

        with st.expander(expander_title, expanded=False):
            if is_complete:
                st.markdown(
                    "<div class='completed-badge'>Conjunto Completo! 🎉</div>",
                    unsafe_allow_html=True,
                )

            if total_items > 0:
                st.progress(
                    progress_val,
                    text=f"Progresso de Coleta: {int(progress_val * 100)}%",
                )
                st.divider()

            if not items_in_set:
                st.write(
                    "Cuidado: Este conjunto **não possui peças** configuradas. Edite para adicionar partes."
                )
            else:
                for key, data in items_in_set.items():
                    base_label = EQUIPMENT_TYPES.get(key, key)
                    custom_name = data.get("custom_name", "").strip()

                    display_label = (
                        f"**{custom_name}** ({base_label})"
                        if custom_name
                        else f"{base_label}"
                    )

                    cb_key = f"cb_{s['id']}_{key}"
                    current_status = data.get("acquired", False)
                    new_status = st.checkbox(
                        display_label, value=current_status, key=cb_key
                    )

                    if new_status != current_status:
                        update_equipment_acquisition(s["id"], key, new_status)
                        st.rerun()

            st.divider()
            col1, col2 = st.columns([1, 1], gap="medium")
            with col1:
                if st.button(
                    "💾 Clonar",
                    key=f"btn_clone_{s['id']}",
                    use_container_width=True,
                ):
                    if clone_equipment_set(s["id"]):
                        st.success("Conjunto clonado com sucesso!")
                        st.rerun()
            with col2:
                if st.button(
                    "✏️ Editar",
                    key=f"btn_edit_{s['id']}",
                    use_container_width=True,
                ):
                    st.session_state.edit_mode_id = s["id"]
                    st.rerun()
