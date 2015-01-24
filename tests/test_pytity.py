# -*- coding: utf-8 -*-

import pytest

from pytity.manager import Manager
from pytity.entity import Entity
from pytity.component import Component
from pytity.processor import EntityProcessor, Processor
from pytity.event import Event


def test_entity_overall_success():
    manager = Manager()
    entity = manager.create_entity()
    component = Component(42)

    entity.add_component(component)
    assert component.value == entity.get_component(Component).value


def test_entity_without_manager_fail():
    entity = Entity(42)
    component = Component(42)

    with pytest.raises(AttributeError):
        entity.add_component(component)

    with pytest.raises(AttributeError):
        entity.get_component(Component)

    with pytest.raises(AttributeError):
        entity.del_component(Component)


def test_entity_del_component_success():
    manager = Manager()
    entity = manager.create_entity()
    component = Component(42)
    entity.add_component(component)

    entity.del_component(Component)
    assert entity.get_component(Component) is None


def test_manager_kill_entity_not_existing_fail():
    manager = Manager()
    entity = Entity(42)

    with pytest.raises(ValueError):
        manager.kill_entity(entity)


def test_manager_kill_entity_remove_component_success():
    manager = Manager()
    entity = manager.create_entity()
    component = Component(42)
    entity.add_component(component)

    manager.kill_entity(entity)

    assert len(list(manager.components_by_type(Component))) == 0


def test_manager_entities_by_types_two_corresponding_success():
    class SpamComponent(Component):
        pass

    manager = Manager()
    entity = manager.create_entity()
    entity.add_component(Component(42))
    entity.add_component(SpamComponent('spam'))

    entities = list(manager.entities_by_types([Component, SpamComponent]))
    assert entity in entities


def test_manager_entities_by_types_two_mixed_success():
    class SpamComponent(Component):
        pass

    manager = Manager()
    entity = manager.create_entity()
    entity.add_component(Component(42))

    entities = list(manager.entities_by_types([Component, SpamComponent]))
    assert entity not in entities


def test_manager_del_component_not_set_dont_fail():
    manager = Manager()
    entity = manager.create_entity()

    entity.del_component(Component)
    assert True


def test_manager_add_processor_success():
    manager = Manager()
    processor = Processor()

    manager.add_processor(processor)
    assert processor is next(manager.processors())


def test_manager_update_processor_inherited_success():
    class SpamEggProcessor(Processor):
        def update(self, delta):
            for entity in self.manager.entities():
                component = entity.get_component(Component)
                component.value = 'egg'

    manager = Manager()
    entity = manager.create_entity()
    entity.add_component(Component('spam'))
    SpamEggProcessor().register_to(manager)

    delta = 0.1
    manager.update(delta)

    assert entity.get_component(Component).value == 'egg'


def test_manager_add_event_success():
    manager = Manager()
    event = Event()

    manager.add_event(event)
    assert event is manager.event_store[Event]


def test_processor_update_fail():
    processor = Processor()

    with pytest.raises(NotImplementedError):
        processor.update(0.1)


def test_processor_publish_not_registered_event_fail():
    manager = Manager()
    processor = Processor()
    processor.register_to(manager)

    with pytest.raises(ValueError):
        processor.publish(Event)


def test_entity_processor_update_entity_fail():
    processor = EntityProcessor()
    entity = Entity(42)

    with pytest.raises(NotImplementedError):
        processor.update_entity(0.1, entity)


def test_entity_processor_update_without_manager_fail():
    processor = EntityProcessor()

    with pytest.raises(AttributeError):
        processor.update(0.1)


def test_entity_processor_update_with_corresponding_needed_set_success():
    class SpamEggProcessor(EntityProcessor):
        def update_entity(self, delta, entity):
            component = entity.get_component(Component)
            component.value = 'egg'

    manager = Manager()
    entity = manager.create_entity()
    entity.add_component(Component('spam'))
    SpamEggProcessor(needed=[Component]).register_to(manager)
    manager.update(0.1)

    assert entity.get_component(Component).value == 'egg'


def test_entity_processor_update_with_not_corresponding_needed_set_fail():
    class SpamEggProcessor(EntityProcessor):
        def update_entity(self, delta, entity):
            component = entity.get_component(Component)
            component.value = 'egg'

    class SpamComponent(Component):
        pass

    manager = Manager()
    entity = manager.create_entity()
    entity.add_component(Component('spam'))
    SpamEggProcessor(needed=[SpamComponent]).register_to(manager)
    manager.update(0.1)

    assert entity.get_component(Component).value == 'spam'


def test_event_call_success():
    class SpamEggEvent(Event):
        def call(self, entity, value):
            component = entity.get_component(Component)
            component.value = value

    class SpamEggProcessor(EntityProcessor):
        def update_entity(self, delta, entity):
            self.publish(SpamEggEvent, entity, 'egg')

    manager = Manager()
    entity = manager.create_entity()
    entity.add_component(Component('spam'))
    SpamEggProcessor().register_to(manager)
    SpamEggEvent().register_to(manager)
    manager.update(0.1)

    assert entity.get_component(Component).value == 'egg'


def test_event_call_fail():
    event = Event()

    with pytest.raises(NotImplementedError):
        event.call()
